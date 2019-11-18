let notifData = [{subject: "Loading...", date: "", body: ""}];
		

function fetchData(){
	$.get("/refreshNotices", function(data, status){
		notifData = JSON.parse(data);
	});
	
	return notifData;
}

$("#notifBody").ready(function(){

	let notifSub     = $("#notifSub");
	let notifDate    = $("#notifDate");
	let notifContent = $("#notifContent");
	let notifDiv     = $("#notif-div");

	let configureTableElements = function(){
		let currNotifData = fetchData();

		currNotifData.forEach(function(notice, index){
			let subj = $("<td></td>").append(notice.subject);
			let date = $("<td></td>").append(notice.date);

			let row  = $("<tr></tr>").append(subj, date);

			$("#notifBody").append(row);
		});

		notifSub.text(currNotifData[0].subject);
		notifDate.text(currNotifData[0].date);
		notifContent.text(currNotifData[0].body);

		$("#notifBody").children().click(function(event){
			let dataIndex = $(this).index();

			notifDiv.fadeOut(200);

			notifSub.text(currNotifData[dataIndex].subject);
			notifDate.text(currNotifData[dataIndex].date);
			notifContent.text(currNotifData[dataIndex].body);

			notifDiv.fadeIn(200);
			console.log(dataIndex);
		});
	};

	let clearTable = function(){
		$("#notifBody").children().remove();
	};
	fetchData();
	setTimeout(function(){
	clearTable();
	configureTableElements();

	}, 1000);

	
	$("#refreshNotif").click(function(){
		$("#notifBody").fadeOut(100);
		clearTable();
		configureTableElements();
		$("#notifBody").fadeIn(100);
	});
});



