// document.addEventListener('DOMContentLoaded', function(){
//     const seasonSelect = document.getElementById('season-select');
//     const text = document.getElementById('notAvailable');
    
//     seasonSelect.addEventListener('change', function(){
//         const selectedSeason = this.value;
        
//         // Check if ANY team has this season using data-season attribute
//         const teamsForSeason = document.querySelectorAll(`[data-season="${selectedSeason}"]`);
//         const hasTeams = teamsForSeason.length > 0;
        
//         if (hasTeams) {
//             // Teams exist - hide "not available" message and show teams
//             text.classList.add('hidden');
//             filterTeamBySeason(selectedSeason);
//         } else {
//             // No teams - show "not available" message and hide all teams
//             text.classList.remove('hidden');
//             filterTeamBySeason(selectedSeason); // This will hide all teams
//         }
//     });
// });

// function filterTeamBySeason(selectedSeason){    
//     const teamItems = document.querySelectorAll('.team-item');
    
//     teamItems.forEach(function(teamItem){
//         const teamSeason = teamItem.getAttribute('data-season');
//         if (selectedSeason === teamSeason) {
//             teamItem.classList.remove('hidden');
//         } else {
//             teamItem.classList.add('hidden');
//         }
//     });
// }           