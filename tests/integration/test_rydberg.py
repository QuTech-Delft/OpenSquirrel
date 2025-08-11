from opensquirrel import Circuit


class TestRydberg:
    def test_circuit(self) -> None:
        circuit = Circuit.from_string(
            """version 3.0

qubit[9] q

asm(Rydberg) '''
INIT(p(0,1)) q[0]
INIT(p(1,1)) q[1]
INIT(p(1,2)) q[2]
INIT(p(2,0)) q[3]
INIT(p(2,1)) q[4]
INIT(p(2,2)) q[5]
INIT(p(3,3)) q[6]
INIT(p(3,1)) q[7]
INIT(p(4,0)) q[8]
'''

X q

asm(Rydberg) '''
RG(r(0.00046748015548948326, -0.9711667423688995, 0.15759622123497696)) q[0]
RG(r(0.001868075691355584, -0.9423334847377992, 0.15759622123497696)) q[0]
RG(r(0.004196259096889474, -0.9135002271066988, 0.15759622123497696)) q[0]
'''

X q
""",
        )
        # Compiler configuration is yet to be defined for the Rydberg backend.
        assert (
            str(circuit)
            == """version 3.0

qubit[9] q

asm(Rydberg) '''
INIT(p(0,1)) q[0]
INIT(p(1,1)) q[1]
INIT(p(1,2)) q[2]
INIT(p(2,0)) q[3]
INIT(p(2,1)) q[4]
INIT(p(2,2)) q[5]
INIT(p(3,3)) q[6]
INIT(p(3,1)) q[7]
INIT(p(4,0)) q[8]
'''
X q[0]
X q[1]
X q[2]
X q[3]
X q[4]
X q[5]
X q[6]
X q[7]
X q[8]
asm(Rydberg) '''
RG(r(0.00046748015548948326, -0.9711667423688995, 0.15759622123497696)) q[0]
RG(r(0.001868075691355584, -0.9423334847377992, 0.15759622123497696)) q[0]
RG(r(0.004196259096889474, -0.9135002271066988, 0.15759622123497696)) q[0]
'''
X q[0]
X q[1]
X q[2]
X q[3]
X q[4]
X q[5]
X q[6]
X q[7]
X q[8]
"""
        )
