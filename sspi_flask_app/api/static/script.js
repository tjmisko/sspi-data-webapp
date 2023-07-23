async function DatabaseStatus(database){
    let response = await fetch('/api/v1/database/' + database +'/status')
}