// Run this code to solve sudoku-problem
conn = new WebSocket('wss://math-tester.herokuapp.com/sudoku-solver/');
conn.onmessage = evt => {
    i=0, j=0, JSON.parse(evt.data).forEach(row => {
        row.forEach(e => {
            $('td')[i*9+j].click();
            $('div[class=numpad-item]')[e-1].click();
            j++; if(j==9){i++; j=0};
        });
    });
};
conn.onopen = evt => conn.send($('#game')[0].innerHTML);
