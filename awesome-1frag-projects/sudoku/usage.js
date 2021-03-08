// Run this code to solve sudoku-problem
let conn = new WebSocket('wss://ifrag.herokuapp.com/sudoku-solver/');
conn.onmessage = evt => {
    let i=0, j=0; JSON.parse(evt.data).forEach(row => {
        row.forEach(e => {
            $('td')[i*9+j].click();
            $('div[class=numpad-item]')[e-1].click();
            j++; if(j===9){i++; j=0}
        });
    });
};
conn.onopen = _ => conn.send($('#game')[0].innerHTML);
