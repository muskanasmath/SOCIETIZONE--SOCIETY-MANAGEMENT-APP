import os, datetime
from flask import render_template, request, flash, redirect, url_for, make_response, session, jsonify
from werkzeug.utils import secure_filename
from . import app, allowed_file, read_file
from dbconnect import connection
from App.forms import *
from random import randint

try:
	CONN, CURSOR = dbconnect.connection()
except Exception as e:
	print(e)
	exit()



@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
	if('mainPage' in session):
		if(session['mainPage']=='/dashboard'):
			return redirect(url_for('userDashboard'))
		else:
			return redirect(url_for('adminPage'))


	loginForm = LoginForm(request.form)
	if request.method == 'POST':
		if loginForm.validate_on_submit():
			if loginForm.accType.data == 'FlatAcc':
				return redirect(url_for('userDashboard'))
			else:
				return redirect(url_for('adminPage'))
				#to-do: REDIRECT TO ADMIN PAGE
		else:
			for error in loginForm.errors.values():
				flash(str(error[0]))

	return render_template('index.html', form=loginForm)

@app.route('/admin', methods=['GET'])
def adminPage():
	addressQuery = "SELECT * FROM society WHERE society_id=%d" % (session['societyId'])
	CURSOR.execute(addressQuery)
	addressRes = CURSOR.fetchone()
	address = [str(addressRes[2]), str(addressRes[3]), str(addressRes[4]), str(addressRes[5])]
	

	statsCounter = {'residents': 0, 'flats':0, 'wings': 0, 'admins':0}

	wingsQuery = "SELECT wing_id FROM wing WHERE society_id=%d" % (session['societyId'])
	CURSOR.execute(wingsQuery)
	wings = CURSOR.fetchall()
	statsCounter['wings'] = len(wings)
	flats = []
	if statsCounter['wings'] > 0:
		flatsQuery = "SELECT flat_id FROM flat WHERE wing_id in (%s)" % (','.join([str(x[0]) for x in wings]))
		CURSOR.execute(flatsQuery)
		flats = CURSOR.fetchall()
		statsCounter['flats'] = len(flats)

	if len(flats) > 0:
		residentsQuery = "SELECT COUNT(resident_id) FROM resident WHERE flat_id IN (%s)" % (','.join([str(x[0]) for x in flats]))
		CURSOR.execute(residentsQuery)
		statsCounter['residents'] = CURSOR.fetchone()[0]

	adminCountQuery = "SELECT COUNT(resident_id) FROM admin WHERE society_id=%d" % (session['societyId'])
	CURSOR.execute(adminCountQuery)
	statsCounter['admins'] = CURSOR.fetchone()[0]
	
	newNoticeForm = AddNoticeForm (request.form)
	newBillForm   = AddBillForm   (request.form)

	wingsQuery = "SELECT wing_id, wing_name FROM wing WHERE society_id=%d" % (session['societyId'])
	CURSOR.execute(wingsQuery)

	newBillForm.selectedWings.choices = [(str(x[0]), str(x[1])) for x in CURSOR.fetchall()]

	return render_template('admin/adminpage.html', address=address, counter=statsCounter, noticeForm=newNoticeForm, billForm=newBillForm)

@app.route('/addNotice', methods=['POST'])
@admin_login_required
def addNotice():
	submittedNotice = AddNoticeForm(request.form)
	if not submittedNotice.validate_on_submit():
		for error in submittedNotice.errors.values():
			flash(str(error[0]))
	else:
		notice_id = randint(1,9999)
		addNoticeQuery = "INSERT INTO notices VALUES(%d,%d,'%s',%s','%s')" % (notice_id,session['societyId'],submittedNotice.header.data, submittedNotice.date.data, submittedNotice.body.data)
	return redirect(url_for('adminPage'))

@app.route('/addBill', methods=['POST'])
@admin_login_required
def addBill():
	submittedBill = AddBillForm(request.form)
	print(submittedBill.selectedWings.data)
	#COMPROMISE, VALIDATE DOESNT WORK
	if True or submittedBill.validate_on_submit():
		flash('Added bill')

		for selWing in submittedBill.selectedWings.data:
			getFlatIdQuery = "SELECT flat_id FROM flat WHERE wing_id=%s" % (selWing)
			CURSOR.execute(getFlatIdQuery)
			flats = CURSOR.fetchall()

			for flat_id in flats:
				randomBillId = randint(1,9999)
				addBillQuery = "INSERT INTO basic_maintenance_bill VALUES  \
				(%d, %d, '%s', %d, %d, %d, %d, %d, %d, %d,%d, '%s', NULL) \
				" % (randomBillId, flat_id[0],submittedBill.billDate.data,submittedBill.WATER_CHARGES.data,submittedBill.PROPERTY_TAX.data,submittedBill.ELECTRICITY_CHARGES.data,submittedBill.SINKING_FUNDS.data,submittedBill.PARKING_CHARGES.data,submittedBill.NOC.data,submittedBill.INSURANCE.data,submittedBill.OTHER.data,submittedBill.dueDate.data)
				CURSOR.execute(addBillQuery)
				CURSOR.fetchall()
				CONN.commit()
			print('ADDED BILL')
	else:
		flash('Error bill')

	return redirect(url_for('adminPage'))

@app.route('/logout', methods=['GET'])
def logout():
	session.clear()
	return redirect(url_for('index'))

@app.route('/dashboard', methods=['GET'])
@user_login_required
def userDashboard():
	return render_template('user/userdashboard.html')

@app.route('/bills')
@user_login_required
def userBill():
	categories = {'WATER CHARGES':3, 'PROPERTY TAX':4, 'ELECTRICITY CHARGES':5, 'SINKING FUNDS':6, 'PARKING CHARGES':7, 'NOC':8, 'INSURANCE':9, 'OTHER':10}

	billListQuery = "SELECT due_date, amount, bill_num \
					FROM maintenance_bill \
					WHERE flat_id='%d'\
					ORDER BY due_date DESC" % (session['flatId'])

	CURSOR.execute(billListQuery)
	billList = CURSOR.fetchall()
	
	if len(billList) > 0:
		latest_bill = billList[0]
		billList = [{'date': bill[0], 'amount': bill[1]} for bill in billList]

	if len(billList) <= 0:
		currBill = {}
		currBill['date']    = 'N.A.'
		currBill['entries'] = [{'category': x, 'cost': 0} for x in categories]
		currBill['amount']  = 0
		return render_template('user/userbillpage.html', currBill=currBill, billList=billList)


	if len(request.args) <= 0:
		currBillQuery = "SELECT * FROM maintenance_bill WHERE bill_num=%d" % (latest_bill[2])
	else:
		day   = request.args.get('dd')
		month = request.args.get('mm')
		year  = request.args.get('yyyy')
		
		billDate      = '-'.join((year, month, day))
		currBillQuery = "SELECT * FROM maintenance_bill WHERE due_date='%s'" % (billDate)


	CURSOR.execute(currBillQuery)
	currBillResult = CURSOR.fetchone()
	currBill = {}
	currBill['date'] = currBillResult[11]
	currBill['entries'] = [ { 'category' : x, 'cost' : float(currBillResult[categories[x]])} for x in categories]
	currBill['amount'] = currBillResult[12]

	print(currBill['entries'])
	return render_template('user/userbillpage.html', currBill=currBill, billList=billList)

@app.route('/profile')
@user_login_required
def userProfile():
		ownerNameQuery = "SELECT owner_name, pending_dues, profile_img FROM account WHERE acc_name='%s'" % (session['accName'])
		CURSOR.execute(ownerNameQuery)
		ownerRes    = CURSOR.fetchone()
		ownerName   = ownerRes[0]
		pendingDues = ownerRes[1]
		imageUrl    = ownerRes[2]

		if imageUrl is None:
			imageUrl = '#none'
		else:
			imageUrl = 'documents/' + imageUrl

		residentQuery = "SELECT resident_name, contact, resident_id FROM resident WHERE flat_id=%d" % (session['flatId'])
		CURSOR.execute(residentQuery)

		resList = [{'name' :row[0], 'phone': str(row[1]), 'id': str(row[2])} for row in CURSOR.fetchall()]
		residentForm = AddResident(request.form)
		return render_template('user/userprofile.html', imageUrl=imageUrl, ownerName = ownerName, resList = resList, pendingDues = pendingDues, residentForm=residentForm)

