from project.problem import Problem
import argparse


class MinimizeProblem(Problem):

    def initialize_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument('--mini', action='store_true', help='minimize the given DFA')

    def is_chosen_problem(self, args):
        return bool(args.mini)

    def run(self, args):
        input_file = args.input
        output_file = args.output

        # 1. Beolvasás
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip() != '']

        if len(lines) < 4:
            raise ValueError("A bemeneti fájlnak legalább 4 sora kell legyen.")

        states = lines[0].split()
        alphabet = lines[1].split()
        start_state = lines[2].strip()
        accept_states = set(lines[3].split())

        # 2. Hibakezelés
        if start_state not in states:
            raise ValueError(f"A kezdőállapot ({start_state}) nem szerepel az állapotok között.")
        for a in accept_states:
            if a not in states:
                raise ValueError(f"A végállapot ({a}) nem szerepel az állapotok között.")

        trans = {}
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
            trans[(src, sym)] = dst

        # 3. Elérhetetlen állapotok eltávolítása (BFS)
        reachable = set()
        stack = [start_state]
        while stack:
            s = stack.pop()
            if s in reachable:
                continue
            reachable.add(s)
            for a in alphabet:
                if (s, a) in trans:
                    stack.append(trans[(s, a)])

        working = [s for s in states if s in reachable]

        # 4. Myhill-Nerode Táblázatkitöltő Algoritmus (Piramis)
        # Bevezetünk egy láthatatlan csapdaállapotot a hiányzó átmenetekhez
        DEAD = "__DEAD__"
        all_states = working + [DEAD]
        
        full_trans = dict(trans)
        for s in all_states:
            for a in alphabet:
                if (s, a) not in full_trans:
                    full_trans[(s, a)] = DEAD

        marked = set()  # Ide kerülnek a megkülönböztethető párok (pl. frozenset({q0, q1}))

        # Alap eset: különböző végállapotúság
        for i in range(len(all_states)):
            for j in range(i + 1, len(all_states)):
                p, q = all_states[i], all_states[j]
                if (p in accept_states) != (q in accept_states):
                    marked.add(frozenset([p, q]))

        # Iteráció (a piramis csillagozása visszamenőleg)
        changed = True
        while changed:
            changed = False
            for i in range(len(all_states)):
                for j in range(i + 1, len(all_states)):
                    p, q = all_states[i], all_states[j]
                    
                    # Ha már meg van jelölve, nem vizsgáljuk tovább
                    if frozenset([p, q]) in marked:
                        continue
                    
                    # Megnézzük az összes betűre az átmeneteket
                    for a in alphabet:
                        p_next = full_trans[(p, a)]
                        q_next = full_trans[(q, a)]
                        
                        # Ha a célállapotok párja már csillagos -> ezt is csillagozzuk
                        if p_next != q_next and frozenset([p_next, q_next]) in marked:
                            marked.add(frozenset([p, q]))
                            changed = True
                            break

        # 5. Összevonás (Union-Find)
        # A csillag nélküli párok összetartoznak
        parent = {s: s for s in all_states}

        def find(s):
            if parent[s] == s:
                return s
            parent[s] = find(parent[s])
            return parent[s]

        def union(p, q):
            root_p = find(p)
            root_q = find(q)
            if root_p != root_q:
                parent[root_p] = root_q

        for i in range(len(all_states)):
            for j in range(i + 1, len(all_states)):
                p, q = all_states[i], all_states[j]
                if frozenset([p, q]) not in marked:
                    union(p, q)

        # Csoportok kinyerése
        classes = {}
        for s in all_states:
            root = find(s)
            classes.setdefault(root, []).append(s)

        # 6. Elnevezés (legkisebb indexű tag neve)
        def state_index(state):
            if state == DEAD:
                return 99999
            i = len(state)
            while i > 0 and state[i-1].isdigit():
                i -= 1
            if i < len(state):
                return int(state[i:])
            return states.index(state)

        final_classes = []
        for cls in classes.values():
            # Ha a csoport csak a csapdaállapotból áll, kidobjuk
            if len(cls) == 1 and cls[0] == DEAD:
                continue
            # Ha vannak valódi állapotok a csoportban, azokat megtartjuk
            real_states = [s for s in cls if s != DEAD]
            min_idx = min(state_index(s) for s in real_states)
            final_classes.append((f"s{min_idx}", real_states, cls))

        # Rendezés a név száma szerint
        final_classes.sort(key=lambda x: int(x[0][1:]))

        # 7. Átmenetek generálása
        state_to_class_name = {}
        for new_name, real_states, _ in final_classes:
            for s in real_states:
                state_to_class_name[s] = new_name

        out_trans = []
        for new_name, real_states, _ in final_classes:
            # A csoportot egy valódi állapot képviseli az átmeneteknél
            rep = real_states[0]
            for a in alphabet:
                # Csak akkor írunk ki átmenetet, ha az EREDETI automatában volt!
                if (rep, a) in trans:
                    target = trans[(rep, a)]
                    target_name = state_to_class_name[target]
                    out_trans.append((new_name, a, target_name))

        # Rendezés: forrás -> szimbólum -> cél
        out_trans.sort(key=lambda t: (int(t[0][1:]), t[1], int(t[2][1:])))

        # 8. Kimeneti fájl összeállítása
        out_states = [name for name, _, _ in final_classes]
        out_alphabet = sorted(alphabet)
        out_start = state_to_class_name[start_state]
        
        out_accept = []
        for name, real_states, _ in final_classes:
            if any(s in accept_states for s in real_states):
                out_accept.append(name)

        out_lines = [
            ' '.join(out_states),
            ' '.join(out_alphabet),
            out_start,
            ' '.join(out_accept)
        ]
        for src, sym, dst in out_trans:
            out_lines.append(f"{src} {sym} {dst}")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(out_lines))