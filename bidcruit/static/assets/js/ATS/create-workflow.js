$(async function() {
        $("#userFacets").sortable({
            connectWith: "ul",
            placeholder: "placeholder",
            delay: 150
        })
        async function getWorkflowData(){
            var return_data = await $.ajax({
                url:"/company/get_workflow_data/",
                headers: {'X-CSRFToken': $("input[name=csrfmiddlewaretoken]").val() },
                type:'POST',
                contentType: 'application/json; charset=UTF-8',
                error: function (request, status, error) {
                }
            }).done(function(response){
                console.log('response>>>>>',response)
            });
            return return_data
        }
        var data = await getWorkflowData();

    var stageList = data['stages_data'];
    var categoryList = data['category_data'];
    var tempList = data['template_data'];
//    var stageList = [{"key":1,"stage_name":"prerequisites"},{"key":2,"stage_name":"JCR"},{"key":3,"stage_name":"reasoning assessment"},{"key":4,"stage_name":"technical assessment"},{"key":5,"stage_name":"general interview"},{"key":6,"stage_name":"ceo round"}];
//
//    var categoryList = [
//        {"stageKey":1,"cate_list":[{"key":101,"cate_name":"UI/UX design"},{"key":102,"cate_name":"Adobe Photoshop"},{"key":103,"cate_name":"HTML/CSS/SASS"}]},
//        {"stageKey":2,"cate_list":[{"key":201,"cate_name":"python"},{"key":202,"cate_name":"django"}]},
//        {"stageKey":3,"cate_list":[{"key":301,"cate_name":"JavaScript"},{"key":302,"cate_name":"Angular"},
//        {"key":303,"cate_name":"React"}]},{"stageKey":4,"cate_list":[{"key":401,"cate_name":"PHP"}]},
//        {"stageKey":5,"cate_list":[{"key":501,"cate_name":"Node JS"},{"key":502,"cate_name":"Android"},{"key":503,"cate_name":"Shift/C#"},{"key":504,"cate_name":"React"}]},
//        {"stageKey":6,"cate_list":[{"key":601,"cate_name":"Test Automation(JAVA)"},{"key":602,"cate_name":"Test Automation(JavaScript)"},{"key":603,"cate_name":"Test Automation(Python)"},{"key":604,"cate_name":"Test Automation(Ruby)"}]}];
//
//    var tempList = [
//    {"cateKey":101,"temp_list":[{"key":1,"temp_name":"template 22510"},{"key":2,"temp_name":"template 22511"},{"key":3,"temp_name":"template 22512"}]},
//    {"cateKey":102,"temp_list":[{"key":1,"temp_name":"template 23001"},{"key":2,"temp_name":"template 23002"},{"key":3,"temp_name":"template 23003"},{"key":4,"temp_name":"template 23004"},{"key":5,"temp_name":"template 23005"},{"key":6,"temp_name":"template 23006"}]},
//    {"cateKey":103,"temp_list":[{"key":1,"temp_name":"template 24001"},{"key":2,"temp_name":"template 24002"},{"key":3,"temp_name":"template 24003"},{"key":4,"temp_name":"template 24004"}]},
//    {"cateKey":201,"temp_list":[{"key":1,"temp_name":"template 30001"},{"key":2,"temp_name":"template 30002"},{"key":3,"temp_name":"template 30003"},{"key":4,"temp_name":"template 30004"}]},
//    {"cateKey":202,"temp_list":[{"key":1,"temp_name":"template 31001"},{"key":2,"temp_name":"template 31002"},{"key":3,"temp_name":"template 31003"}]},
//    {"cateKey":301,"temp_list":[{"key":1,"temp_name":"template 40001"},{"key":2,"temp_name":"template 40002"},{"key":3,"temp_name":"template 40003"},{"key":4,"temp_name":"template 40004"},{"key":5,"temp_name":"template 40005"},{"key":6,"temp_name":"template 40006"}]},{"cateKey":302,"temp_list":[{"key":1,"temp_name":"template 41001"},{"key":2,"temp_name":"template 41002"},{"key":3,"temp_name":"template 41003"}]},{"cateKey":303,"temp_list":[{"key":1,"temp_name":"template 42001"},{"key":2,"temp_name":"template 42002"},{"key":3,"temp_name":"template 42003"},{"key":4,"temp_name":"template 42004"},{"key":5,"temp_name":"template 42005"}]},{"cateKey":401,"temp_list":[{"key":1,"temp_name":"template 50001"},{"key":2,"temp_name":"template 50002"},{"key":3,"temp_name":"template 50003"},{"key":4,"temp_name":"template 50004"},{"key":5,"temp_name":"template 50005"},{"key":6,"temp_name":"template 50006"}]},{"cateKey":501,"temp_list":[{"key":1,"temp_name":"template 60001"},{"key":2,"temp_name":"template 60002"},{"key":3,"temp_name":"template 60003"}]},{"cateKey":502,"temp_list":[{"key":1,"temp_name":"template 61001"},{"key":2,"temp_name":"template 61002"},{"key":3,"temp_name":"template 61003"},{"key":4,"temp_name":"template 61004"}]},{"cateKey":503,"temp_list":[{"key":1,"temp_name":"template 62001"},{"key":2,"temp_name":"template 62002"}]},{"cateKey":504,"temp_list":[{"key":1,"temp_name":"template 63001"},{"key":2,"temp_name":"template 63002"},{"key":3,"temp_name":"template 63003"},{"key":4,"temp_name":"template 63004"},{"key":5,"temp_name":"template 63005"}]},{"cateKey":601,"temp_list":[{"key":1,"temp_name":"template 70001"}]},{"cateKey":602,"temp_list":[{"key":1,"temp_name":"template 71001"},{"key":2,"temp_name":"template 71002"},{"key":3,"temp_name":"template 71003"}]},{"cateKey":603,"temp_list":[{"key":1,"temp_name":"template 72001"},{"key":2,"temp_name":"template 72002"},{"key":3,"temp_name":"template 72003"},{"key":4,"temp_name":"template 72004"}]},{"cateKey":604,"temp_list":[{"key":1,"temp_name":"template 73001"},{"key":2,"temp_name":"template 73002"},{"key":3,"temp_name":"template 73003"},{"key":4,"temp_name":"template 73004"},{"key":5,"temp_name":"template 73005"}]}];

    dragBoxShow();
    /***workflow selector listing***/
    stageListPopulate(stageList);
    $('#stageSelectorList').on('change',function(){ //stage selector event
        var getStageId = $(this).find('option:selected').val();
        if(getStageId !== ''){
            var cateListData = {'id':getStageId,'data':categoryList};
            cateListPopulate(cateListData);
            $('#templateSelectorList option').remove();
            $('#templateSelectorList').append(`<option label="Select Template"></option>`);
            $('#templateSelectorList').attr('disabled','');
        }else{
            $('#categorySelectorList option,#templateSelectorList option').remove();
            $('#categorySelectorList,#templateSelectorList').attr('disabled','');
            $('#categorySelectorList').append(`<option label="Select Category"></option>`);
            $('#templateSelectorList').append(`<option label="Select Template"></option>`);
        }
    })

    $('#categorySelectorList').on('change',function(){ //category selector event
        var getCatId = $(this).find('option:selected').val();
        if(getCatId !== ''){
            var templistData = {'id':getCatId,'data':tempList}
            tempListPopulate(templistData);
        }else{
            $('#templateSelectorList option').remove();
            $('#templateSelectorList').append(`<option label="Select Template"></option>`);
            $('#templateSelectorList').attr('disabled','')
        }
    })

    $('#Addworkflow').on('click',function(){ //add & update new stage workflow list
        var getListIdArr = [];
        var listCounter = 0;
        if($('#userFacets li').length == '0'){
            listCount = 0;
        }else{
            //listCount = parseInt($('#userFacets li:last-child').attr('id')) + 1;
            $('#userFacets li').each(function(){
                var listEleId = parseInt($(this).attr('id'))
                getListIdArr.push(listEleId)
            })
            listCounter = Math.max.apply(Math, getListIdArr);
            listCounter = listCounter + 1
        }
        dragBoxShow();

        console.log('list count>>' +listCounter)
        var getStageInputs = $('#stageSelectorList').find('option:selected');
        var getCatInputs = $('#categorySelectorList').find('option:selected');
        var getTempInputs = $('#templateSelectorList').find('option:selected');
        var stageName = $('.edu-name').val()
        var validFlag = false
        if(getStageInputs.val() == ''){
            $('#stageSelectorList').addClass('valid')
            validFlag = true;
            setTimeout(function(){$('#stageSelectorList').removeClass('valid')},2000)
        }
        if(getCatInputs.val() == ''){
            $('#categorySelectorList').addClass('valid')
            validFlag = true;
            setTimeout(function(){$('#categorySelectorList').removeClass('valid')},2000)
        }
        if(getTempInputs.val() == ''){
            $('#templateSelectorList').addClass('valid')
            validFlag = true;
            setTimeout(function(){$('#templateSelectorList').removeClass('valid')},2000)
        }
        if(stageName == ''){
            $('.edu-name').addClass('valid')
            validFlag = true;
            setTimeout(function(){$('.edu-name').removeClass('valid')},2000)
        }
        if(validFlag == false){
            var cloneList = `<li class="facet" id="`+listCounter+`">
                                <div class="title_stages_name">
                                    <div class="name_list_h" data-sname="`+stageName+`">Stages Name : `+stageName+`</div>
                                    <div class="edit_delete_action">
                                        <a href="javascript:void(0);" class="edit-btn"><i class="fas fa-edit"></i></a>
                                        <a href="javascript:void(0);" class="remove-btn"><i class="fas fa-trash-alt"></i></a>
                                    </div>
                                </div>
                                <div class="info_data stage-ls" data-sid="`+getStageInputs.val()+`" data-stitle="`+getStageInputs.text()+`">Stage Type  : `+getStageInputs.text()+`</div>
                                <div class="info_data category-ls" data-cid="`+getCatInputs.val()+`" data-ctitle="`+getCatInputs.text()+`">Category : `+getCatInputs.text()+`</div>
                                <div class="info_data temp-ls" data-tempid="`+getTempInputs.val()+`" data-temptitle="`+getTempInputs.text()+`">Template : `+getTempInputs.text()+`</div>
                            </li>`;
            
            $('#userFacets').append(cloneList);
            resetForm();
        }
    })

    $(document).on('click','.edit-btn',function(){ //edit stage List
       /* var listClosestEle = $(this).closest('li');
        var listId = $(this).closest('li').attr('id');
        
        var stageId = listClosestEle.find('.stage-ls').data('sid')
        var cateId = listClosestEle.find('.category-ls').data('cid')
        var tempId = listClosestEle.find('.temp-ls').data('tempid')

        $.each($("#stageSelectorList option"),function(){
            if($(this).val() == stageId){
                $(this).prop('selected',true)
                var updateCatList = {'id':stageId,'data':categoryList}
                cateListPopulate(updateCatList);

                $.each($("#categorySelectorList option"),function(){
                   //prop select of edit category list
                })
            }
        })

        $('.add_stages_box .workflow_add_btn')
        .find('button')
        .attr('id','updateWorkFlow')
        .text('Update')
        .attr('data-id',listId)*/
    })
    $(document).on('click','.remove-btn',function(){ //remove stage List
        $(this).closest('li.facet').remove();
        dragBoxShow();
    })

    $('#Save_and_Next').on('click',function(){
        var worflow_name = $("#worflow_name").val();
        if(worflow_name == ""){
            alert("Please Enter Worflow Name");
            $( "#worflow_name" ).focus();
            return false;
        }
        var saveListItem = [];
        var listSize = $('#userFacets li').length
        if(listSize !== '0'){
            $("#userFacets li").each(function(keyID){
               var stageName = $(this).find('.name_list_h').data('sname');
                var stageId = $(this).find('.stage-ls').data('sid');
                var stageTitle = $(this).find('.stage-ls').data('stitle');
                var catId = $(this).find('.category-ls').data('cid');
                var catTitle = $(this).find('.category-ls').data('ctitle');
                var tempId = $(this).find('.temp-ls').data('tempid');
                var tempTitle = $(this).find('.temp-ls').data('temptitle');
                var newItem = {
                    "stage_name":stageName,
                    "stage_id":stageId,
                    "stage_title":stageTitle,
                    "cate_id":catId,
                    "cate_title":catTitle,
                    "temp_id":tempId,
                    "temp_title":tempTitle
                }
                saveListItem.push(newItem)
            })
            console.log(JSON.stringify(saveListItem));
            if(edit_flag){
                var url = "/company/edit_workflow/"+w_id;
                console.log('url edit>>>',url)
            }else{
                var url = "/company/create_workflow/";
            }
            $.ajax({
                url:url,
                headers: {'X-CSRFToken': $("input[name=csrfmiddlewaretoken]").val() },
                type:'POST',
                contentType: 'application/json; charset=UTF-8',
                data: JSON.stringify({data:saveListItem,name: worflow_name}),
                error: function (request, status, error) {
                }
            }).done(function(response){
                if(response == 'True'){
                    window.location = 'http://localhost:8000/company/workflow_configuration/';
                }else{
                    alert('something went wrong !!');
                }
            });
        }

    })

});

/****Functions****/
function stageListPopulate(getStageList){
    optHtml = '';
    if(getStageList.length){
        $.each(getStageList, function(i){
            optHtml += `<option class="text-capitalize" value="`+getStageList[i].key+`">`+getStageList[i].stage_name+`</option>`;
        })
        $('#stageSelectorList').append(optHtml);
    }
}

function cateListPopulate(getListingItems){
    var optCateHtml = '';
    var getSelectedStageId = getListingItems.id;
    var getCateItemList = getListingItems.data;
    if(getCateItemList.length){
        $('#categorySelectorList option').remove()
        $.each(getCateItemList,function(cKey){
            if(getCateItemList[cKey].stageKey == getSelectedStageId){
                var cateDataItems  = getCateItemList[cKey].cate_list;
                if(cateDataItems.length){
                    optCateHtml +=`<option label="Select Category"></option>`;
                    $.each(cateDataItems,function(keyId){
                        optCateHtml += `<option value="`+cateDataItems[keyId].key+`">`+cateDataItems[keyId].cate_name+`</option>`;
                    })
                }
                $('#categorySelectorList').append(optCateHtml);
            }
        })
        $('#categorySelectorList').removeAttr('disabled')
    }
}

function tempListPopulate(getTempListItems){
    var optCateHtml = '';
    var getSelectedCateId = getTempListItems.id;
    var getTempItemList = getTempListItems.data;
    //console.log(getSelectedCateId)
    //console.log(getTempItemList)
    if(getTempItemList.length){
        $('#templateSelectorList option').remove()
        $.each(getTempItemList,function(cKey){
            if(getTempItemList[cKey].cateKey == getSelectedCateId){
                var tempDataItems  = getTempItemList[cKey].temp_list;
                if(tempDataItems.length){
                    optCateHtml +=`<option label="Select Template"></option>`;
                    $.each(tempDataItems,function(keyId){
                        optCateHtml += `<option value="`+tempDataItems[keyId].key+`">`+tempDataItems[keyId].temp_name+`</option>`;
                    })
                }
                $('#templateSelectorList').append(optCateHtml);
            }
        })
        $('#templateSelectorList').removeAttr('disabled')
    }
}

function resetForm(){
    $('#stageSelectorList').prop("selectedIndex", 0).val();
    $('#categorySelectorList option, #templateSelectorList option').remove()
    $('#categorySelectorList, #templateSelectorList').attr('disabled','')
    $('#categorySelectorList').append('<option label="Select Category"></option>')
    $('#templateSelectorList').append('<option label="Select Template"></option>')
    $('.edu-name').val('')
}

function dragBoxShow(){
    if($('#userFacets li').length > 1){
        $('.drag-box').hide()
    }else{
        $('.drag-box').show()
    }
}



			