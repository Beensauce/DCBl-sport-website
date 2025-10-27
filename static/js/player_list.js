document.addEventListener('DOMContentLoaded', function() {
    const nav = document.getElementById('team-nav');
    const results = document.querySelector('.games');
    const upcomings = document.querySelector('.upcoming');

    function handleClick(event){
        event.preventDefault();

        nav.querySelectorAll('.tabs').forEach(tab => {
            tab.classList.remove('underline');
        })

        const target = event.target.closest('.tabs')
        target.classList.add('underline');
        
        if (target.innerText == 'Results'){
            results.style.display = 'block';
            upcomings.style.display = 'none';
        }
        else{
            upcomings.style.display = 'block';
            results.style.display = 'none';
        }
    }

    nav.addEventListener('click', handleClick);
});
