from project.problem import Problem

import argparse

class DFAProblem(Problem):
    def initialize_parser(self, parser: argparse.ArgumentParser):
        """
        Initialize the parser with the necessary arguments
        """
        parser.add_argument('--check', help='check word(s), separated by commas (a,ab,aab,abbb)')

    def is_chosen_problem(self, args):
        """
        Check if the problem is chosen
        """
        return bool(args.check)

    def run(self, args):
        """
        Run the program
        """
        # Access the input and output file paths
        input_file = args.input
        output_file = args.output
        words = args.check.split(',')
    
        # Read the numbers
        with open(input_file, 'r') as f_in:
            lines = [line.strip() for line in f_in if line.strip() != '']

        states = set(lines[0].split(' ')) #possible states
        alphabet = set(lines[1].split(' ')) #possible symbols
        start_state = lines[2].strip()
        accept_states = set(lines[3].split(' ')) #final_states

        transitions = {}
        for line in lines[4:]:
            from_state, symbol, to_state = line.split(' ')
            transitions[(from_state, symbol)] = to_state

        results = []
        for word in words:
            current_state = start_state
            accepted = True

            for symbol in word:
                if (current_state, symbol) not in transitions:
                    accepted = False
                    break
                current_state = transitions[(current_state, symbol)]
                
            if accepted and current_state in accept_states:
                results.append("IGEN")
            else:
                results.append("NEM")

        with open(output_file, 'w') as f_out:
            f_out.write('\n'.join(results))
            