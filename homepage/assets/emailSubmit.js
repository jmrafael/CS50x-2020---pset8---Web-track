function submitIt()
{
    //Receiving the values
    var name = document.getElementById('name').value;
    var email = document.getElementById('email').value;
    var telephone = document.getElementById('telephone').value;
    var subject = document.getElementById('subject').value;
    var message = document.getElementById('message').value;
    submitOK = "true";

    //Little validations and alert
    if (name.length < 2 || telephone.length < 2 || message.length < 2) {
        alert("Please fill a valid name, email, telephone, subject or message!");
        submitOK = "false";
    } else
    {
        alert('Congratulations '+ name + '. Your message has been sent successfully.');
    }
}



