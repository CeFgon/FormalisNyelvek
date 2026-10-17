from project.problem import Problem

import argparse

class DeterminizeProblem(Problem):
    def initialize_parser(self, parser: argparse.ArgumentParser):
        """
        Initialize the parser with the necessary arguments
        """
        parser.add_argument('--det', action='store_true', help='determinize the given automaton')

    def is_chosen_problem(self, args):
        """
        Check if the problem is chosen
        """
        return bool(args.det)

    def run(self, args):
        """
        Run the program
        """
        # Access the input and output file paths
        input_file = args.input
        output_file = args.output
    
        #1. Bemeneti fajl beolvasasa (ures sorokat kihagyva)
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip() != '']

        if len(lines) < 4:
            raise ValueError("A bemeneti fájlnak legalább 4 sora kell legyen.")

        states = lines[0].split() #possible states
        alphabet = lines[1].split() #possible symbols
        start_state = lines[2].strip()
        accept_states = set(lines[3].split()) #final_states

        #2. hibakezeles
        if start_state not in states:
            raise ValueError(f"A kezdőállapot ({start_state}) nem szerepel az állapotok között.")
        for a in accept_states:
            if a not in states:
                raise ValueError(f"A végállapot ({a}) nem szerepel az állapotok között.")

        #3. NFA atmenetek beolvasasa: (allapot, szimbolum) -> halmaz
        nfa_trans = {}
        for line in lines[4:]:
            parts = line.split()
            if len(parts) != 3:
                raise ValueError(f"Hibás átmenet sor: {line}")
            src, sym, dst = parts
            if src not in states:
                raise ValueError(f"Ismeretlen forrásállapot: {src}")
            if dst not in states:
                raise ValueError(f"Ismeretlen célállapot: {dst}")
            if sym not in alphabet:
                raise ValueError(f"Ismeretlen szimbólum: {sym}")
            nfa_trans.setdefault((src, sym), set()).add(dst)

        #4. reszhalmaz-konstrukcio
        start_subset = frozenset([start_state])
        state_order = []          # a részhalmazok létrehozási sorrendben
        name_map = {}             # részhalmaz -> s0, s1, ...

        def get_name(subset):
            if subset not in name_map:
                name_map[subset] = f"s{len(state_order)}"
                state_order.append(subset)
            return name_map[subset]

        get_name(start_subset)
        queue = [start_subset]
        dfa_trans = []            # (forrás_név, szimbólum, cél_név)

        while queue:
            current = queue.pop(0)
            current_name = name_map[current]

            for sym in sorted(alphabet):
                next_set = set()
                for state in current:
                    if (state, sym) in nfa_trans:
                        next_set.update(nfa_trans[(state, sym)])

                if next_set:  # üres halmazt nem vesszük fel
                    next_fs = frozenset(next_set)
                    if next_fs not in name_map:
                        get_name(next_fs)
                        queue.append(next_fs)
                    dfa_trans.append((current_name, sym, name_map[next_fs]))
                # ha üres, az átmenetet kihagyjuk

        #5. Vegallapotok meghatarozasa
        accept_names = []
        for subset in state_order:
            if subset & accept_states:   # metszet nem üres
                accept_names.append(name_map[subset])
        accept_names.sort(key=lambda x: int(x[1:]))

        #6. Atmenetek rendezese: forras, majd szimbolum, majd cel szerint
        def trans_key(t):
            src, sym, dst = t
            return (int(src[1:]), sym, int(dst[1:]))

        dfa_trans.sort(key=trans_key)

        #7. Kimeneti fajl
        out_lines = []
        out_lines.append(' '.join(name_map[subset] for subset in state_order))
        out_lines.append(' '.join(sorted(alphabet)))
        out_lines.append('s0')
        out_lines.append(' '.join(accept_names))
        for src, sym, dst in dfa_trans:
            out_lines.append(f"{src} {sym} {dst}")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(out_lines))