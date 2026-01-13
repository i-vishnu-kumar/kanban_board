document.addEventListener('DOMContentLoaded', function() {
    let errorMessage = document.querySelector('.wring_creds_pop_up');
    let loginStatus = errorMessage.getAttribute('is_login_success');
    console.log("login staus"+ loginStatus)
    if (loginStatus === 'False') {
      errorMessage.style.display = 'block';
    }
    else {
        errorMessage.style.display = 'none'; 
    }
  });
  
