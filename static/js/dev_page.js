let sprintItems = document.querySelectorAll('li');

sprintItems.forEach(item => {
    // let mopName = item.getAttribute('data-mop-name');
    // let startDate = item.getAttribute('data-start-date');
    const maxCompleted = parseInt(item.getAttribute('data-max-completed'), 10);
    const total = parseInt(item.getAttribute('data-total'), 10);

    let completion = (maxCompleted / total) * 100;

    const progressBar = document.createElement('div');
    progressBar.className = 'progress-container';
    progressBar.style.height = `${completion}%`; 

    item.appendChild(progressBar);
});
