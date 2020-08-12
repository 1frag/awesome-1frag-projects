/*
def _solve(field):
    def wrapper(i, j):
        if i == 9 and j == 0:
            return True
        next_i, next_j = (i + 1, 0) if (j == 8) else (i, j + 1)
        if field[i][j] is not None:
            return wrapper(next_i, next_j)
        for k in range(1, 10):
            field[i][j] = str(k)
            if check(field) and wrapper(next_i, next_j):
                return True
        field[i][j] = None
        return False
    return wrapper(0, 0)
*/

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <string>
#include <iostream>

using namespace std;
namespace py = pybind11;

bool check(vector<vector<optional<string>>> field) {
    auto _check = [](vector<optional<string>>q) {
        set<string>st = {};
        int sz = 0;
        for (auto e : q) {
            if (e) {
                st.insert(e.value()); //add
                sz++;
            }
        }
        return sz == int(st.size());
    };
    for (auto l : field)
	    if (!_check(l)) return false;

    for (int i=0;i<9;i++) {
        vector<optional<string>>v = {};
        for (auto l : field)
            v.push_back(l[i]);
        if (!_check(v)) return false;
    }

    for (int i=0;i<3;i++)
        for(int j=0;j<3;j++)
            if (!_check({
                field[3*i][3*j], field[3*i+1][3*j], field[3*i+2][3*j],
                field[3*i][3*j+1], field[3*i+1][3*j+1], field[3*i+2][3*j+1],
                field[3*i][3*j+2], field[3*i+1][3*j+2], field[3*i+2][3*j+2]
            }))
                return false;
    return true;
}

optional<vector<vector<optional<string>>>> solve(
        vector<vector<optional<string>>> field
) {
    vector<vector<optional<string>>> field_ = field;
    function<bool(int, int)> wrapper;
    wrapper = [&field_, &wrapper](int i, int j) {
        if (i == 9 && j == 0) return true;
        int next_i = i, next_j = j + 1;
        if (next_j == 9) {next_j = 0; next_i++;}
        if (field_[i][j]) return wrapper(next_i, next_j);
        for(int k=1;k<=9;k++) {
            field_[i][j] = to_string(k);
            if (check(field_) && wrapper(next_i, next_j))
                return true;
            field_[i][j] = nullopt;
        }
        return false;
    };
    if (!wrapper(0, 0)) return {};
    return field_;
}

PYBIND11_MODULE(sudoku, m) {
    m.def("check", &check, "Validate field");
    m.def("solve", &solve, "Solve sudoku");
}
