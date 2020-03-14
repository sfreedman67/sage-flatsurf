r"""
Function to compute the number field generated by some elements in a given
number field.

This is likely to be merge in later Sage versions, see

    https://trac.sagemath.org/ticket/29331
"""
from sage.rings.rational_field import QQ
from sage.modules.free_module import VectorSpace
from sage.matrix.constructor import matrix
from sage.categories.homset import Hom
from sage.categories.fields import Fields
from sage.rings.qqbar import do_polred

def subfield_from_elements(self, alpha, name=None, polred=True, threshold=None):
    r"""
    Return the subfield generated by the elements ``alpha``.

    INPUT:

    - ``alpha`` - list of elements in this number field

    - ``name`` - a name for the generator of the new number field

    - ``polred`` (boolean, default ``True``) - whether to optimize the generator of
      the newly created field

    - ``threshold`` (positive number, default ``None``) - threshold to be passed to
      the ``do_polred`` function

    EXAMPLES::

        sage: from flatsurf.geometry.subfield import subfield_from_elements

        sage: x = polygen(QQ)
        sage: poly = x^4 - 4*x^2 + 1
        sage: emb = AA.polynomial_root(poly, RIF(0.51, 0.52))
        sage: K.<a> = NumberField(poly, embedding=emb)
        sage: sqrt2 = -a^3 + 3*a
        sage: sqrt3 = -a^2 + 2
        sage: assert sqrt2 ** 2 == 2 and sqrt3 ** 2 == 3
        sage: L, elts, phi = subfield_from_elements(K, [sqrt2, 1 - sqrt2/3])
        sage: L
        Number Field in a0 with defining polynomial x^2 - 2 with a0 = 1.414213562373095?
        sage: elts
        [a0, -1/3*a0 + 1]
        sage: phi
        Ring morphism:
          From: Number Field in a0 with defining polynomial x^2 - 2 with a0 = 1.414213562373095?
          To:   Number Field in a with defining polynomial x^4 - 4*x^2 + 1 with a = 0.5176380902050415?
          Defn: a0 |--> -a^3 + 3*a
        sage: assert phi(elts[0]) == sqrt2
        sage: assert phi(elts[1]) == 1 - sqrt2/3

        sage: L, elts, phi = subfield_from_elements(K, [1, sqrt3])
        sage: assert phi(elts[0]) == 1
        sage: assert phi(elts[1]) == sqrt3

    TESTS::

        sage: from flatsurf.geometry.subfield import subfield_from_elements
        sage: x = polygen(QQ)

        sage: p = x^8 - 12*x^6 + 23*x^4 - 12*x^2 + 1
        sage: K.<a> = NumberField(p)
        sage: sqrt2 = 6/7*a^7 - 71/7*a^5 + 125/7*a^3 - 43/7*a
        sage: sqrt3 = 3/7*a^6 - 32/7*a^4 + 24/7*a^2 + 10/7
        sage: sqrt5 = 8/7*a^6 - 90/7*a^4 + 120/7*a^2 - 27/7
        sage: assert sqrt2**2 == 2 and sqrt3**2 == 3 and sqrt5**2 == 5
        sage: L, elts, phi = subfield_from_elements(K, [sqrt2, sqrt3], name='b')
        sage: assert phi(elts[0]) == sqrt2
        sage: assert phi(elts[1]) == sqrt3
        sage: L, elts, phi = subfield_from_elements(K, [sqrt2, sqrt5], name='b')
        sage: assert phi(elts[0]) == sqrt2
        sage: assert phi(elts[1]) == sqrt5
        sage: L, elts, phi = subfield_from_elements(K, [sqrt3, sqrt5], name='b')
        sage: assert phi(elts[0]) == sqrt3
        sage: assert phi(elts[1]) == sqrt5
        sage: L, elts, phi = subfield_from_elements(K, [-149582/214245 + 21423/5581*sqrt2], name='b')
        sage: assert L.polynomial() == x^2 - 2
        sage: L, elts, phi = subfield_from_elements(K, [131490/777 - 1359/22*sqrt3], name='b')
        sage: assert L.polynomial() == x^2 - 3
        sage: L, elts, phi = subfield_from_elements(K, [12241829/177 - 321121/22459 * sqrt5], name='b')
        sage: assert L.polynomial() == x^2 - x - 1

        sage: from sage.rings.qqbar import number_field_elements_from_algebraics
        sage: R.<x> = QQ[]
        sage: p1 = x^3 - x - 1
        sage: roots1 = p1.roots(QQbar, False)
        sage: for _ in range(10):
        ....:     p2 = R.random_element(degree=2)
        ....:     while not p2.is_irreducible(): p2 = R.random_element(degree=2)
        ....:     roots2 = p2.roots(QQbar, False)
        ....:     K, (a1,b1,c1,a2,b2), phi = number_field_elements_from_algebraics(roots1 + roots2)
        ....:     u1 = 1 - a1/17 + 3/7*a1**2
        ....:     u2 = 2 + 33/35 * a1
        ....:     L, (v1,v2), phi = subfield_from_elements(K, [u1, u2], threshold=100)
        ....:     assert L.polynomial() == p1
        ....:     assert phi(v1) == u1 and phi(v2) == u2
    """
    V = VectorSpace(QQ, self.degree())
    alpha = [self(a) for a in alpha]

    # Rational case
    if all(a.is_rational() for a in alpha):
        return (QQ, [QQ(a) for a in alpha], self.coerce_map_from(QQ))

    # Saturate with multiplication
    vecs = [a.vector() for a in alpha]
    U = V.subspace(vecs)
    modified = True
    while modified:
        modified = False
        d = U.dimension()
        if d == self.degree():
            return (self, alpha, Hom(self, self, Fields()).identity())
        B = U.basis()
        for i in range(d):
            for j in range(i, d):
                v = (self(B[i]) * self(B[j])).vector()
                if v not in U:
                    U += V.subspace([v])
                    modified = True

    # Strict subfield, find a generator
    vgen = None
    for b in U.basis():
        if self(b).minpoly().degree() == d:
            vgen = b
            break
    if vgen is None:
        s = 1
        while True:
            vgen = U.random_element(proba=0.5, x=-s, y=s)
            if self(vgen).minpoly().degree() == d:
                break
            s *= 2

    # Minimize the generator via PARI polred
    gen = self(vgen)
    p = gen.minpoly()
    if polred:
        if threshold:
            fwd, back, q = do_polred(p, threshold)
        else:
            fwd, back, q = do_polred(p)
    else:
        q = p
        fwd = back = self.polynomial_ring().gen()

    new_gen = fwd(gen)
    assert new_gen.minpoly() == q
    K, hom = self.subfield(new_gen, name=name)

    # need to express the elements in the basis 1, a, a^2, ..., a^(d-1)
    M = matrix(QQ, [(new_gen**i).vector() for i in range(d)])
    new_alpha = [K(M.solve_left(elt.vector())) for elt in alpha]

    return (K, new_alpha, hom)
