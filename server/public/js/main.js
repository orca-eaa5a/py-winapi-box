function onFileSelected(elem){
    let text_elem = document.getElementById("selected_file_name");
    let input_elem = elem;
    let fname = input_elem.files[0].name;
    text_elem.value = fname;
}