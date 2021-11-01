//var demo_data = [{"template-data":[{"question_label":"Question1","option_list":[{"option_label":"1","option_value":"next","questions":[]},{"option_label":"2","option_value":"add-question","questions":[{"question_label":"sub que1-2.1","option_list":[{"option_label":"1.1","option_value":"exit","questions":[]},{"option_label":"1.2","option_value":"next","questions":[]}]}]},{"option_label":"3","option_value":"exit","questions":[]}]},{"question_label":"question2","option_list":[{"option_label":"22","option_value":"exit","questions":[]},{"option_label":"33","option_value":"next","questions":[]}]}]}];
var question_data=''
var demo_data =[]
var current_question = null
$(document).ready(function(){

    demo_data=[get_prequisites()]
    console.log(demo_data)
    question_data = demo_data[0]['template-data']
    current_question = question_data.shift()
    update_question_box(current_question)
})

function update_question_box(question)
{
//  var question_text = document.getElementById("question_text")
//  question_text.value = current_question['question_label']
//  var question_box = document.getElementById("current_question")
//  var all_options =current_question['option_list']
  /*for(var i in  all_options)
  {
    console.log("iiiiiiiii",all_options[i])
    var option_label = all_options[i]['option_label']
    var option_value = all_options[i]['option_value']
    $(question_box).append(`<div class="option_box">
        <input type="radio" name="pre_requisite_option" class="pre_requisite_option" id="option_`+i+`" value="`+option_value+`">
        <label for="pre_requisite_option">`+option_label+`</label>
      </div>`)
  }*/
 $('.Question_listing .question_listing_inner').remove();
  var questViewer = "";
  questViewer += `<div class="question_listing_inner">

        <div class="question_text">`+question.question_label+`</div>
        <div class="question_option_box">
                <div class="radio-group gender-select mg-t-10">
                    <div class="option_tab_q">`;
                    for(var i in  question.option_list){
                        var option_label = question.option_list[i]['option_label']
                        var option_value = question.option_list[i]['option_value']
                        questViewer +=  `<label class='rdiobox'>
                                            <input id="option_`+i+`" name="pre_requisite_option" type="radio" value="`+option_value+`" data-parsley-multiple="basic_radio">
                                            <span>`+option_label+`</span>
                                        </label>`;
                       }
        questViewer += `</div></div></div></div>`;

$('.Question_listing').append(questViewer)
  //console.log('show queUI::',questViewer)
}


function next_step()
{

  var selected_option = $('input[name="pre_requisite_option"]:checked')[0]

  if(selected_option.value == "next")
  {

    current_question = question_data.shift()

    if(typeof(current_question) == 'undefined')
    {

      console.log("uiasdas")
      document.write("YOU ARE HIRED")
    }
    document.querySelectorAll('.option_tab_q').forEach(e => e.remove());
    update_question_box(current_question)

    // document.write("you failed")
  }
  else  if(selected_option.value == "add-question")
  {

    current_option_index = selected_option.id.split("option_")[1]
    console.log(current_option_index)
    console.log(current_question["option_list"][current_option_index]["questions"])
    current_question = current_question["option_list"][current_option_index]["questions"][0]
    document.querySelectorAll('.option_tab_q').forEach(e => e.remove());
    update_question_box(current_question)

  }
  else
  {
  alert('failed');
    document.write("failed")
  }
}

