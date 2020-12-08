document.getElementById("Investigatesubmit").addEventListener("click",
async function investigateasync () {
    event.preventDefault();


    // document.getElementById("spinnernmap").style.visibility = "visible";
    try {
        const response = await fetch('/investigate',
            {
                method: 'GET',
                cache: "no-cache",
            })
        await response.text()
            .then((data) => {

                $('#collapseInvestigate3')[0].style.visibility = "visible";
                // document.getElementById("spinnernmap").style.visibility = "hidden";
                document.getElementById("Investigate_response").innerHTML=data
            })
    } catch {
        console.log('error in fetching posts')
    }
})

document.getElementById("headers_submit").addEventListener("click",
async function fetchAsync () {
     event.preventDefault(); 
//    let attacker = document.getElementById('attacker');
//     let target = document.getElementById('target');

    let payload = {
        // attacker: attacker.value,
        //  target: target.value,
        dummy: 'not-required'
    };

    let response = await fetch('/headers',
        {
            method: 'POST',
            body: JSON.stringify(payload),
            cache: "no-cache",
            headers: new Headers
            ({
                "content-type": "application/json"
            })
        })
    await response.json()
        .then(data => {
            $('#headings_output')[0].style.visibility = "visible";
            console.log(data);
            string = JSON.stringify(data, undefined, 2);
            $('#headers_response').html(string)
        })
    .catch(reason => console.log(reason.message))
})

document.getElementById("submit").addEventListener("click",
function start () {
    $('.collapse').collapse("hide")
    $('#successAlert').hidden
    $('#errorAlert').hidden
    $('#collapsExploit3').collapse("hide")
    $('#collapseLateral3').collapse("hide")
    $('#Exploit_response').html("")
    $('.multi-collapse4').collapse("show")

})

document.getElementById("phase1-control").addEventListener("click", function showsection1() {
    $('#collapse-section1')[0].style.visibility="visible"
})