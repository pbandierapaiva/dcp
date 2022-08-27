
function carregaHosts() {
  const xhttp = new XMLHttpRequest();
  xhttp.onload = onLoadHosts;
  xhttp.open("GET", "/hosts");	
  xhttp.send();
}

function onLoadHosts(){

    for (i of JSON.parse(this.responseText)) {
   	
   	barraStatus = document.createElement("div")
   	barraStatus.className = "w3-bar w3-block"
   	
    	ipmi = document.createElement("a")
    	ipmi.className = "w3-button w3-tiny w3-center w3-padding-small w3-border w3-round "
    	ipmi.style = "width:15%"
    	ipmi.href = "http://"+i.redes.ipmi
    	ipmi.target="_blank"
    	ipmi.innerHTML = "IPMI"
    	
    	tipo = document.createElement("a")
    	tipo.className = "w3-button w3-padding-small w3-tiny w3-border w3-center w3-round "
    	tipo.style = "width:10%"
	switch( i.tipo ){
		case "H":
			tipo.innerHTML = "H"
			tipo.className += "w3-blue"
			break
		case "S":
			tipo.innerHTML = "S"
			tipo.className += "w3-teal"
			break
		default:
			tipo.innerHTML = "??"
			break
		}
			
    	estadoHost = document.createElement("span")
    	estadoHost.innerHTML = "&nbsp;"
    	estadoHost.className="w3-button w3-padding-small w3-tiny w3-border w3-round "
    	estadoHost.style = "width:3%"
      	if( i.estado==0 ) estadoHost.className+="w3-grey"
    	else {
    		if(i.estado==1) estadoHost.className+="w3-green"
    		else estadoHost.className+="w3-yellow"
    		}
    	nomeHost = document.createElement("span")
    	nomeHost.innerHTML = i.nome  
    	nomeHost.className="w3-button w3-padding-small w3-tiny w3-border w3-round "
    	nomeHost.style = "width:40%"

    	barraStatus.appendChild(nomeHost)
    	barraStatus.appendChild(ipmi)
    	barraStatus.appendChild(tipo)
	barraStatus.appendChild(estadoHost)
    	
    	item = document.createElement("div")
    	item.className="w3-bar-item w3-small w3-padding-small w3-button"		
	item.onclick = hostinfo       //('/hosts/'+i.id)
	item.target='infoarea'
	item.quem = '/hosts/'+i.id
    	item.appendChild(barraStatus)

    	document.getElementById("listahost").appendChild(item)
    }
  }
  
function hostinfo(ev) {
  	const xhttp = new XMLHttpRequest();
	xhttp.onload = onInfoHostLoaded;
	xhttp.open("GET", ev.currentTarget.quem);	
	xhttp.send();
	}


function onInfoHostLoaded(){
	campos = JSON.parse(this.responseText)
	
	// alert(this.responseText)
	
	tit = document.getElementById("hititle")
	tit.innerHTML = "Host info: "+campos["nome"]

	area = document.getElementById("infoarea")
	area.innerHTML = ""  // remove tudo da área antes de preencher
	
   	form = document.createElement("form")
    	form.className = "w3-container"
   	
   	cpo1l = document.createElement("label")
   	cpo1l.innerHTML = "Nome"
   	form.appendChild(cpo1l)
   	cpo1 = document.createElement("input")
   	cpo1.value = campos["nome"]
   	cpo1.className = "w3-input w3-border"
   	cpo1.disabled = true
   	form.appendChild(cpo1)
   	   	
   	cpo2l = document.createElement("label")
   	cpo2l.innerHTML = "Estado"
   	form.appendChild(cpo2l)
    	cpo2pa = document.createElement("p")
   	cpo2a = document.createElement("input")
   	cpo2a.type = "radio"
   	cpo2a.name = "restado" 
   	cpo2a.value = "1"
   	if( campos["estado"]=="1" )
   		cpo2a.checked = true
   	cpo2a.className = "w3-radio"
   	cpo2a.disabled = true
   	cpo2al = document.createElement("label")
   	cpo2al.innerHTML = "ON"
   	cpo2pa.appendChild(cpo2a)
   	cpo2pa.appendChild(cpo2al)
   	form.appendChild(cpo2pa)
   	
    	cpo2pb = document.createElement("p")   	
   	cpo2b = document.createElement("input")
   	cpo2b.type = "radio"
   	cpo2b.name = "restado" 
   	cpo2b.value = "0"
   	if( campos["estado"]=="0" )
   		cpo2b.checked = true
   	cpo2b.className = "w3-radio"
   	cpo2b.disabled = true
   	cpo2bl = document.createElement("label")
   	cpo2bl.innerHTML="OFF"
	cpo2pb.appendChild(cpo2b)
   	cpo2pb.appendChild(cpo2bl)
   	form.appendChild(cpo2pb)

   	solabel = document.createElement("label")
   	solabel.innerHTML = "Sistema operacional"
   	form.appendChild(solabel)
   	cposo = document.createElement("input")
   	cposo.value = campos["so"]
   	cposo.className = "w3-input w3-border"
   	cposo.disabled = true
   	form.appendChild(cposo)

   	kernlabel = document.createElement("label")
   	kernlabel.innerHTML = "Kernel"
   	form.appendChild(kernlabel)
   	cpokern = document.createElement("input")
   	cpokern.value = campos["kernel"]
   	cpokern.className = "w3-input w3-border"
   	cpokern.disabled = true
   	form.appendChild(cpokern)
   	   	
   	tipo = document.createElement("div")
   	tipo.className = "w3-tag w3-margin w3-padding "
   	tipo.style = "width:200px"
   	switch( campos["tipo"] ) {
   	case "H":  // HOST
    		tipo.innerHTML = "Host"
    		tipo.className+= "w3-green" 
   		break
   	case "S":  // Standalone
   		tipo.innerHTML = "Standalone"
    		tipo.className+= "w3-teal"
   		break
   	case "V":  // Máq. virtual
   		tipo.innerHTML = "VM"   		
    		tipo.className+= "w3-blue"
   		break
   	case "U":  // Desconhecido
     		tipo.innerHTML = "desconhecido"
    		tipo.className+= "w3-grey"
   		break
   		}
   	//tipo.innerHTML = campos["tipo"]
   	form.appendChild(tipo)
   	
   	redes = document.createElement("p") 
   	redes.innerHTML = "<label>Interfaces: </label>"
   	for (const key of Object.keys( campos["redes"] )) {
   		tag = document.createElement("div")
   		tag.className = "w3-tag w3-margin "
   		tag.style ="width:120px"
   		tag.innerHTML = campos["redes"][key]
   		switch( key ) {
   			case "ipmi":
   				tag.className+="w3-black"
   				break
   			case "164":
   				tag.className+="w3-green"
   				break
   			case "160":
   				tag.className+="w3-lime"
   				break
   			case "core":
   				tag.className+="w3-blue"
   				break
   			case "under":
   				tag.className+="w3-teal"
   				break
   			case "dmz":
   				tag.className+="w3-red"
   				break
   			default:
   				tag.className+="w3-grey"
   			}
   		redes.appendChild(tag)
   		}
   	form.appendChild(redes)
   	
   	area.appendChild(form)
   	
   	
   	
	}
   	

