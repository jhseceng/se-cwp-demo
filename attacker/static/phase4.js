// document.getElementById("falconInstallSubmit").addEventListener("click",
//     async function installFalconasync() {
//         event.preventDefault();
//
//         // let time_interval = document.getElementById('time_interval').value;
//         empty_array = []
//         let package_name = $('#package_name').val();
//         let action = $('#action').val();
//         let instance_ids = $('#instance_ids').val();
//         let document_name = $('#document_name').val();
//         if (instance_ids.length == 0) {
//             alert('Please select an AWS instance')
//             return
//         }
//         $('#install_falcon_out')[0].style.visibility = "hidden"
//         //$('#query_vpc_out')[0].style.display = "none"
//         document.getElementById("spinnerfalconinstall").style.visibility = "visible";
//
//         let payload = {
//             package_name: package_name,
//             action: action,
//             instance_ids: instance_ids,
//             document_name: document_name
//         };
//         try {
//             const response = await fetch('/installfalcon',
//                 {
//                     method: 'POST',
//                     cache: "no-cache",
//                     body: JSON.stringify(payload),
//                     headers: new Headers
//                     ({
//                         "content-type": "application/json"
//                     })
//                 })
//             await response.json()
//                 .then((data) => {
//                         document.getElementById("spinnerfalconinstall").style.visibility = "hidden";
//                         $('#install_falcon_response').html(data.Result);
//                         //$('#query_vpc_out')[0].style.display = "block"
//                         $('#install_falcon_out')[0].style.visibility = "visible"
//                     }
//                 )
//         } catch {
//             console.log('error in fetching posts')
//         }
//     })
$(document).ready(queryHostsasync().then((data) => console.log('loaded')));


document.getElementById("drawHostTableSubmit").addEventListener("click", function getHostinfo() {
    event.preventDefault()
    $("#hostQueryTable tr").remove()
    $('#query_host_out')[0].style.visibility = "hidden"
    //$('#query_vpc_out')[0].style.display = "none"
    document.getElementById("spinnerHostQuery").style.visibility = "visible";
    queryHostsasync()
        .then((data) => {
            // $('#hostquery_response').html(out);
            $('#query_host_out')[0].style.visibility = "visible";
            $('#falconformInstallSubmit')[0].style.visibility = "visible";
            $('#collapse6Query1').collapse()
            console.log("Table refresh complete")
        })
})

async function queryHostsasync() {

    function generateTableHead(table, data) {
        let thead = table.createTHead();
        let row = thead.insertRow();
        for (let key of data) {
            let th = document.createElement("th");
            let text = document.createTextNode(key);
            th.appendChild(text);
            row.appendChild(th);
        }
        let th = document.createElement("th");
        let text = document.createTextNode('Action');
        th.appendChild(text);
        row.appendChild(th);
    }

    function generateTable(table, data) {
        for (let element of data) {
            let row = table.insertRow();
            for (key in element) {
                let cell = row.insertCell();
                let text = document.createTextNode(element[key]);
                cell.appendChild(text);
            }
            const install_options = [{"action": "None"}, {"action": "Install"}, {"action": "Uninstall"}]
            let selectList = document.createElement("select");
            selectList.setAttribute("id", "installFalconSelect");
            const options = ["Install", "Uninstall", "None"]
            for (var j = 0; j < options.length; j++) {
                var option = document.createElement("option");
                option.setAttribute("value", options[j]);
                if (options[j] == "None") {
                    option.setAttribute("selected", true);
                }
                option.text = options[j];
                selectList.appendChild(option);
            }
            let cell = row.insertCell();
            cell.appendChild(selectList);

        }

    }

    $("#hostQueryTable tr").remove()

    try {
        const response = await fetch('/showinstances',
            {
                method: 'GET',
                cache: "no-cache",
            })
        await response.json()
            .then((data) => {
                    document.getElementById("spinnerHostQuery").style.visibility = "hidden";
                    let out = JSON.stringify(data);
                    let table = document.getElementById("hostQueryTable");
                    let table_data = Object.keys(data[0]);
                    generateTableHead(table, table_data);
                    generateTable(table, data);

                    return
                }
            )
    } catch {
        console.log('error in fetching posts')
    }
}


document.getElementById("falconformInstallSubmit").addEventListener("click",
    async function falconInstall() {
        event.preventDefault();
        let install_instances = [];
        //uninstall_instances will be an array of json objects containing
        // {"instanceid": instanceid, "aid": aid}
        let uninstall_instances = [];
        let payload = {};
        const table = document.getElementById("hostQueryTable");
        let row;
        for (let i = 1; i < table.rows.length; ++i) {
            row = table.rows[i];
            let instanceId = row.cells[2].innerText;
            let aid = row.cells[5].innerText;
            let instance_action = row.cells[8].childNodes[0].value;
            if (instance_action == "Install") {
                install_instances.push(instanceId);
            } else if (instance_action == "Uninstall") {
                instanceId = {"instanceId": instanceId, "aid": aid}
                uninstall_instances.push(instanceId);
            }
        }

        let package_name = $('#package_name').val();
        let document_name = $('#document_name').val();
        if (uninstall_instances.length != 0) {
            payload = {
                package_name: package_name,
                action: "Uninstall",
                instance_ids: uninstall_instances,
                document_name: document_name
            }
        }
        if (install_instances.length != 0) {
            payload = {
                package_name: package_name,
                action: "Install",
                instance_ids: install_instances,
                document_name: document_name
            }
        }
        if (uninstall_instances.length == 0 && install_instances.length == 0) {
            alert("Select Instance for Install/Uninstall")
            return
        }
        document.getElementById("spinnerfalconinstall").style.visibility = "visible";
        sendSsmCommand(payload)
            .then((data) => {
                    let sendSsmCommandResult = data;

                    console.log(sendSsmCommandResult)
                    //            data = {"Result": cmd_status,"message": msg}
                    if (data.Result === "Success") {
                        console.log(data.Result)
                        // queryHostsasync().then((data) => console.log("table refresh complete"))
                        $('#query_host_out')[0].style.visibility = "visible";
                        document.getElementById("spinnerfalconinstall").style.visibility = "hidden";
                        $('#falconformInstallSubmit')[0].style.visibility = "visible";
                        $('#collapse6Query1').collapse()
                    }
                }
            )
            .catch(reason => console.log(reason.message))
    })


async function sendSsmCommand(payload) {
    try {
        const response = await fetch('/installfalcon',
            {
                method: 'POST',
                cache: "no-cache",
                body: JSON.stringify(payload),
                headers: new Headers
                ({
                    "content-type": "application/json"
                })
            })
        let data = await response.json()
        return data

    } catch {
        console.log('error in fetching posts')
    }
}

document.getElementById("queryGdSubmit").addEventListener("click",
    async function queryGuardDutyasync() {
        event.preventDefault();
        let treeroot = document.getElementById('treeroot');

        while (treeroot.firstChild) {
            treeroot.removeChild(treeroot.firstChild);
        }
        let gdEventsToFilter = $('#guardDutyEventsSelect').val();
        let payload = {
            instanceList: gdEventsToFilter

        };
        try {
            const response = await fetch('/gdquerybyfilter',
                {
                    method: 'POST',
                    cache: "no-cache",
                    body: JSON.stringify(payload),
                    headers: new Headers
                    ({
                        "content-type": "application/json"
                    })
                })
            await response.json()
                .then((data) => {
                    let results = data.results
                    for (index = 0; index < results.length; ++index) {
                        datastr = JSON.stringify(results[index]);
                        jsonView.format(datastr, '.root');
                    }
                })
        } catch {
            console.log('error in fetching posts')
        }

    })