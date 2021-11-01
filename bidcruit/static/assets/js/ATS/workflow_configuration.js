$(document).ready(function(){
//console.log('workflow page loaded...');
appendSubmitActButton();
$("#interviewerList").select2({
    closeOnSelect : false,
    placeholder : "Placeholder"
    // allowHtml: true,
    // allowClear: true,
    // tags: true
});
})


function appendSubmitActButton(){
    console.log('append submit button')
    var finishButtonVisible = "";
    finishButtonVisible += `<div class="col-12 footer_section">
                                <div class="action_btn_section">
                                    <button class="btn btn-sm btn-primary" id="submit" type="button">Save &amp; Finish</button>
                                </div>
                            </div>`; 
    $(".tab-content tab-pane:last-child row col-12:last-child").after(finishButtonVisible);
}
    