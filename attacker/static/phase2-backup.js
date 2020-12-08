document.getElementById("falconInstallSubmit").addEventListener("click",
    async function installFalconasync() {
        event.preventDefault();

        // let time_interval = document.getElementById('time_interval').value;
        empty_array = []
        let package_name = $('#package_name').val();
        let action = $('#action').val();
        let instance_ids = $('#instance_ids').val();
        let document_name = $('#document_name').val();
        if (instance_ids.length == 0) {
            alert('Please select an AWS instance')
            return
        }
        $('#install_falcon_out')[0].style.visibility = "hidden"
        //$('#query_vpc_out')[0].style.display = "none"
        document.getElementById("spinnerfalconinstall").style.visibility = "visible";

        let payload = {
            package_name: package_name,
            action: action,
            instance_ids: instance_ids,
            document_name: document_name
        };
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
            await response.json()
                .then((data) => {
                        document.getElementById("spinnerfalconinstall").style.visibility = "hidden";
                        $('#install_falcon_response').html(data.Result);
                        //$('#query_vpc_out')[0].style.display = "block"
                        $('#install_falcon_out')[0].style.visibility = "visible"
                    }
                )
        } catch {
            console.log('error in fetching posts')
        }
    })


document.getElementById("queryHostsSubmit").addEventListener("click",
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
                let cell = row.insertCell();
                let text = document.createTextNode("Install");
                cell.appendChild(text);
            }

        }

        event.preventDefault();
        $("#hostQueryTable tr").remove()
        $('#query_host_out')[0].style.visibility = "hidden"
        //$('#query_vpc_out')[0].style.display = "none"
        document.getElementById("spinnerHostQuery").style.visibility = "visible";

        try {
            const response = await fetch('/showinstances',
                {
                    method: 'GET',
                    cache: "no-cache",
                })
            await response.json()
                .then((data) => {
                        document.getElementById("spinnerHostQuery").style.visibility = "hidden";
                        let out = JSON.stringify(data)
                        let table = document.getElementById("hostQueryTable");
                        let table_data = Object.keys(data[0]);
                        generateTableHead(table, table_data);
                        generateTable(table, data);
                        $('#hostquery_response').html(out);

                        //$('#query_vpc_out')[0].style.display = "block"
                        $('#query_host_out')[0].style.visibility = "visible"
                    }
                )
        } catch {
            console.log('error in fetching posts')
        }
    })


// let table = document.getElementById("hostQueryTable");
// let table_data = Object.keys(data[0]);
// generateTableHead(table, table_data);
// generateTable(table_data, data);

