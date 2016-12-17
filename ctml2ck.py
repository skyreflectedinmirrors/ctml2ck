from ck2cti import Parser
import os
from cantera import Solution

def main(argv):
    import getopt
    import sys

    longOptions = ['input=', 'thermo=', 'transport=', 'id=', 'output=',
                   'permissive', 'help', 'debug', 'mask=']

    try:
        optlist, args = getopt.getopt(argv, 'dh', longOptions)
        options = dict()
        for o,a in optlist:
            options[o] = a

        if args:
            raise getopt.GetoptError('Unexpected command line option: ' +
                                     repr(' '.join(args)))

    except getopt.GetoptError as e:
        print('ck2cti.py: Error parsing arguments:')
        print(e)
        print('Run "ctml2ck.py --help" to see usage help.')
        sys.exit(1)

    parser = Parser()

    if not options or '-h' in options or '--help' in options:
        #parser.showHelp()
        print """ctml2ck.py: Convert reduced Cantera-format mechanisms to Chemkin input files

Usage:
    ctml2ck --input=<filename>
           [--thermo=<filename>]
           [--transport=<filename>]
           [--id=<phase-id>]
           [--output=<filename>]
           [--permissive]
           [-d | --debug]
           [--mask=<filename>]

Example:
    ctml2ck --input=chem.inp --thermo=therm.dat --transport=tran.dat --mask=mask.txt

If the output file name is not given, an output file with the same name as the
input file, with the extension changed to '.cti'.

The '--permissive' option allows certain recoverable parsing errors (e.g.
duplicate transport data) to be ignored.

The '--mask option expects a reduced Cantera mechanism'

"""
        sys.exit(0)

    if '--input' in options:
        inputFile = options['--input']
    else:
        print('Error: no mechanism input file specified')
        sys.exit(1)

    if '--output' in options:
        outName = options['--output']
    else:
        outName = "reducedmech.txt"

    permissive = '--permissive' in options
    thermoFile = options.get('--thermo')
    transportFile = options.get('--transport')
    phaseName = options.get('--id', 'gas')

    parser.convertMech(inputFile, thermoFile, transportFile, phaseName,
                       'temp.cti', permissive=permissive)
    
    gas = Solution('temp.cti')
    mask = Solution(options.get('--mask'))

    all_lines = []
    with open(inputFile) as infile:
        all_lines = infile.readlines()

    with open (outName, "w+") as file:
        file.write("ELEMENTS\n")
        for element in gas.element_names:
            file.write(element + "\n")
        file.write("END\nSPECIES\n")
        count = 0
        for species in gas.species_names:
            try:
                index = mask.species_index(species)
                file.write(species.ljust(16, " "))
                count += 1
                if count % 5 == 0:
                    count = 0
                    file.write("\n")
            except:
                pass

        file.write("\nEND\nREACTIONS\n")
        all_eqs = gas.reaction_equations()
        for reaction in mask.reaction_equations():
            match = [i for i in range(len(all_eqs)) if all_eqs[i] == reaction]
            if len(match) == 0:
                continue
            match = match[0]

            write_lines = []
            if match < gas.n_reactions - 1:
                write_lines += all_lines[parser.reactions[match].line_number - 1:parser.reactions[match + 1].line_number - 1]
            else:
                write_lines += all_lines[parser.reactions[match].line_number - 1:]
            for line in write_lines:
                file.write(line)

    os.remove("temp.cti")
    os.remove("temp.xml")

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
