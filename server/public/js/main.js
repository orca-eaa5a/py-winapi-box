function onFileSelected(elem){
    let text_elem = document.getElementById("selected_file_name");
    let input_elem = elem;
    let fname = input_elem.files[0].name;
    text_elem.value = fname;
}

function uploadSelectedFile(id, name){
    let elem = $('#'+id);
    let data = new FormData();
    data.append(name, elem[0].files[0]);
    fetch('/upload', {
        method: 'POST',
        cache: 'no-cache',
        body: data
    })
    .then(response => response.json())
    .then((data)=>{
        if(data.success === true){
            window.location.href = '/board';
        }
    })
    $('#'+id);
}