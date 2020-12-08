document.getElementById("exploit_submit").addEventListener("click",
function submitlaunch() {
    event.preventDefault()
    document.getElementById("successAlert").style.display="none";
    document.getElementById("errorAlert").style.display="none";
    document.getElementById("spinner").style.visibility = "visible";
    document.getElementsByClassName("Exploit-output")[0].style.visibility = "collapse";
   // let target = document.getElementById('target');

    let entry = {
        dummy: 'not-required'
    };
   fetch('/launch', {
       method: 'POST',
       body: JSON.stringify(entry),
       cache: "no-cache",
       headers: new Headers({
           "content-type": "application/json"
       })
   })
       .then(function (response) {
           document.getElementById("spinner").style.visibility = "hidden";
           if (response.status !== 200) {
               console.log('Bad Response: $(response.status)');
               $('#errorAlert').text('Bad HTTP Response').show();
               return;
           }
           response.json().then(function (data) {
               if (data.result == 'success') {
                   $('#errorAlert').hidden;
                   $('#successAlert').text(data.message).show();
                   string = JSON.stringify(data, undefined, 2);
                    $('#Exploit_response').html(string);
                    document.getElementsByClassName("Exploit-output")[0].style.visibility = "visible";
               } else {
                   $('#successAlert').hidden;
                   $('#errorAlert').text(data.message).show();
               }

               console.log(data)
           })
       })
})

document.getElementById("send_submit").addEventListener("click",
function submitsend() {
    event.preventDefault()
   function handleResponseStatusAndContentType(response) {
        document.getElementById('spinnerlatmove').style.visibility = 'hidden';
           document.getElementById('collapseLateral3').style.visibility = 'visible';
       const contentType = response.headers.get('content-type');

       if (response.status === 401) throw new Error('Request was not authorized.');

       if (contentType === null) return new Promise(() => null);
       else if (contentType.startsWith('application/json')) {
           response = response.json()
               .then((data) => {
                   $('#errorAlertcmd').text(data.message).show();
                   console.log(response)
               })
       } else if (contentType.startsWith('text/plain')) {
           response = response.text()
               .then((response) => {
                   $('#lateral_response').html(response)
               })
       } else throw new Error(`Unsupported response content-type: ${contentType}`);
   }

   let commandselected = ''
   if (document.getElementById('disabledFieldsetCheck').checked == true){
       commandselected = $('#customCommandInput').val()
   }
   else
       {
       commandselected = $('#cmdtosend').val()
   }

   let entry = {
       cli: commandselected
   };
   let val = JSON.stringify(entry)
    document.getElementById('spinnerlatmove').style.visibility = 'visible';
   document.getElementById('collapseLateral3').style.visibility = 'hidden';
   fetch('/send', {
       method: 'POST',
       body: JSON.stringify(entry),
       cache: "no-cache",
       headers: new Headers({
           "content-type": "application/json"
       })
        })
       .then(response => handleResponseStatusAndContentType(response))
           .catch(error => {
               console.error(error);
               return error;
       })
})





    // // let time_interval = document.getElementById('time_interval').value;
    // empty_array = []
    // let package_name = $('#package_name').val();
    // let action = $('#action').val();
    // let instance_ids = $('#instance_ids').val();
    // let document_name = $('#document_name').val();
    // if (instance_ids.length == 0) {
    //     alert('Please select an AWS instance')
    //     return
    // }
    // $('#install_falcon_out')[0].style.visibility="hidden"
    // //$('#query_vpc_out')[0].style.display = "none"
    // document.getElementById("spinnerfalconinstall").style.visibility = "visible";
    //
    // let payload = {
    //     package_name: package_name,
    //     action: action,
    //     instance_ids: instance_ids,
    //     document_name: document_name
    // };
    // try {
    //     const response = await fetch('/installfalcon',
    //         {
    //             method: 'POST',
    //             cache: "no-cache",
    //             body: JSON.stringify(payload),
    //             headers: new Headers
    //             ({
    //                 "content-type": "application/json"
    //             })
    //         })
    //     await response.json()
    //         .then((data) => {
    //             document.getElementById("spinnerfalconinstall").style.visibility = "hidden";
    //             $('#install_falcon_response').html(data.Result);
    //             //$('#query_vpc_out')[0].style.display = "block"
    //             $('#install_falcon_out')[0].style.visibility = "visible"
    //         }
    //     )
    // }
    // catch{
    //     console.log('error in fetching posts')
    // }

