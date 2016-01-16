"""
Functions for generating quantum objects.
"""

import numpy as np
import scipy.sparse as sp
from quijy.core import qonvert, nrmlz, kron, kronpow, eyepad, eye


def basis_vec(dir, dim, sparse=False):
    """
    Constructs a unit ket that points in dir of total dimensions dim
    """
    if sparse:
        return sp.csr_matrix(([1.0], ([dir], [0])),
                             dtype=complex, shape=(dim, 1))
    else:
        x = np.zeros([dim, 1], dtype=complex)
        x[dir] = 1.0
    return x


def sig(xyz, sparse=False):
    """
    Generates one of the three Pauli matrices, 0-X, 1-Y, 2-Z
    """
    if xyz in (1, 'x', 'X'):
        return qonvert([[0, 1], [1, 0]], sparse=sparse)
    elif xyz in (2, 'y', 'Y'):
        return qonvert([[0, -1j], [1j, 0]], sparse=sparse)
    elif xyz in (3, 'z', 'Z'):
        return qonvert([[1, 0], [0, -1]], sparse=sparse)
    elif xyz in (0, 'i', 'I'):
        return qonvert([[1, 0], [0, 1]], sparse=sparse)


def bell_state(s):
    """
    Generates one of the four bell-states;
    0: phi+, 1: phi-, 2: psi+, 3: psi- (singlet)
    """
    if s in (3, 'psim'):
        return qonvert([0, 1, -1, 0], 'ket') / 2.0**0.5
    elif s in (0, 'phip'):
        return qonvert([1, 0, 0, 1], 'ket') / 2.0**0.5
    elif s in (1, 'phim'):
        return qonvert([1, 0, 0, -1], 'ket') / 2.0**0.5
    elif s in (2, 'psip'):
        return qonvert([0, 1, 1, 0], 'ket') / 2.0**0.5


def singlet():
    """ Alias for one of bell-states """
    return bell_state(3)


def bloch_state(ax, ay, az, purify=False, sparse=False):
    if purify:
        ax, ay, az = np.array([ax, ay, az])/np.sqrt(ax**2 + ay**2 + az**2)
    rho = 0.5 * (sig('i') + ax * sig('x') + ay * sig('y') + az * sig('z'))
    return rho if not sparse else qonvert(rho, sparse=sparse)


# functions
def random_psi(n):
    """
    Generates a wavefunction with random coefficients, normalised
    """
    psi = 2.0 * np.matrix(np.random.rand(n, 1)) - 1
    psi = psi + 2.0j * np.random.rand(n, 1) - 1.0j
    return nrmlz(psi)


def random_rho(n):
    """
    Generates a random density matrix of dimension n, no special properties
    other than being guarateed hermitian, positive, and trace 1.
    """
    rho = 2.0 * np.matrix(np.random.rand(n, n)) - 1
    rho = rho + 2.0j * np.matrix(np.random.rand(n, n)) - 1.0j
    rho = rho + rho.H
    return nrmlz(rho * rho)


def random_product_state(n):
    """
    Calculates the wavefunction of n many random pure qubits.
    """
    # Generator
    def calc_rand_pure_qubits(n):
        for i in range(n):
            u = np.random.rand()
            v = np.random.rand()
            phi = 2 * np.pi * u
            theta = np.arccos(2 * v - 1)
            yield np.matrix([[np.cos(theta / 2.0)],
                             [np.sin(theta / 2.0) * np.exp(1.0j * phi) ]])
    return kron(*[x for x in calc_rand_pure_qubits(n)])


def neel_state(n):
    binary = '01' * (n / 2)
    binary += (n % 2 == 1) * '0'  # add trailing spin for odd n
    return basis_vec(int(binary, 2), 2 ** n)


def singlet_pairs(n):
    return kronpow(bell_state(3), (n / 2))


def werner_state(p):
    return p * bell_state(3) * bell_state(3).H + (1 - p) * np.eye(4) / 4


def ghz_state(n):
    return (basis_vec(0, 2**n) + basis_vec(2**n - 1, 2**n))/2.0**0.5


def ham_heis(n, jx=1, jy=1, jz=1, bz=0, periodic=False, sparse=False):
    """ Constructs the heisenberg spin 1/2 hamiltonian
    Input:
        n: number of spins
        jx, jy, jz: coupling constants, with convention that positive =
        antiferromagnetic
        bz: z-direction magnetic field
        periodic: whether to couple the first and last spins
        sparse: whether to return the hamiltonian in sparse form
    Returns:
        ham: hamiltonian as matrix
    """
    dims = [2] * n
    sds = (jx * kron(sig('x', sparse=True), sig('x', sparse=True)) +
           jy * kron(sig('y', sparse=True), sig('y', sparse=True)) +
           jz * kron(sig('z', sparse=True), sig('z', sparse=True)) -
           bz * kron(sig('z', sparse=True), eye(2)))
    # Begin with last spin, not covered by loop
    ham = eyepad(-bz * sig('z', sparse=True), dims, n - 1)
    for i in range(n - 1):
        ham = ham + eyepad(sds, dims[:-1], i)
    if periodic:
        ham = ham + eyepad(sig('x', sparse=True), dims, [0, n - 1])  \
                  + eyepad(sig('y', sparse=True), dims, [0, n - 1])  \
                  + eyepad(sig('z', sparse=True), dims, [0, n - 1])
    if not sparse:
        ham = ham.todense()  # always construct sparse though
    return ham