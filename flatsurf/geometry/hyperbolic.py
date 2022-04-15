r"""
Two dimensional hyperbolic geometry.

EXAMPLES::

    sage: from flatsurf.geometry.hyperbolic import HyperbolicPlane

    sage: H = HyperbolicPlane(QQ)

"""
######################################################################
#  This file is part of sage-flatsurf.
#
#        Copyright (C) 2022 Julian Rüth
#                      2022 Sam Freedman
#
#  sage-flatsurf is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 2 of the License, or
#  (at your option) any later version.
#
#  sage-flatsurf is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with sage-flatsurf. If not, see <https://www.gnu.org/licenses/>.
######################################################################

from sage.structure.parent import Parent
from sage.structure.element import Element
from sage.structure.unique_representation import UniqueRepresentation


class HyperbolicPlane(Parent, UniqueRepresentation):
    r"""
    The hyperbolic plane over a base ring.

    We do not use a fixed representation of the hyperbolic plane internally.
    However, we mostly think of this as the upper half plane in the Poincaré
    model.

    All objects in the plane must be specified over the given base ring. Note
    that, in some representations, objects might appear to live in a larger
    ring. E.g., when specifying a line by giving a midpoint and the square of
    its radius in the half plane model, then the ideal endpoints of this line
    might have coordinates in the ring after adjoining a square root.

    The implemented elements of the plane are convex subsets such as (finite
    and infinite) points, geodesics, closed half planes, and closed convex
    polygons.

    INPUT:

    - ``base_ring`` -- a base ring for the coefficients defining the equations
      of geodesics in the plane; defaults to the rational field if not
      specified.

    - ``category`` -- the category for this object; if not specified, defaults
      to sets with partial maps. Note that we do not use metric spaces here
      since the elements of this space are convex subsets of the hyperbolic
      plane and not just points so the elements do not satisfy the assumptions
      of a metric space.

    EXAMPLES::

        sage: from flatsurf.geometry.hyperbolic import HyperbolicPlane

        sage: HyperbolicPlane()
        Hyperbolic Plane over Rational Field

    """

    @staticmethod
    def __classcall__(cls, base_ring=None, category=None):
        from sage.all import QQ
        base_ring = base_ring or QQ

        from sage.categories.all import SetsWithPartialMaps
        category = category or SetsWithPartialMaps()

        return super(HyperbolicPlane, cls).__classcall__(cls, base_ring=base_ring, category=category)

    def __init__(self, base_ring, category):
        super().__init__(category=category)
        self._base_ring = base_ring

    def base_ring(self):
        r"""
        Return the base ring over which objects in the plane are defined.

        EXAMPLES::

            sage: from flatsurf.geometry.hyperbolic import HyperbolicPlane

            sage: HyperbolicPlane().base_ring()
            Rational Field

        """
        return self._base_ring

    def infinity(self):
        r"""
        Return the point at infinity in the Poincaré half plane model.
        """
        return self.projective(1, 0)

    def real(self, r):
        r"""
        Return the ideal point ``r`` on the real axis in the Poincaré half
        plane model.
        """
        return self.projective(r, 1)

    def projective(self, p, q):
        r"""
        Return the ideal point with projective coordinates ``[p: q]`` in the
        Poincaré half plane model.
        """
        raise NotImplementedError

    def half_circle(self, center, radius_squared):
        r"""
        Return the geodesic centered around the real ``center`` and with
        ``radius_squared`` in the Poincaré half plane model. The geodesic is
        oriented such that the point at infinity is to its left.

        Use the ``-`` operator to pass to the geodesic with opposite
        orientation.
        """
        raise NotImplementedError

    def vertical(self, real):
        r"""
        Return the vertical geodesic at the ``real`` ideal point in the
        Poincaré half plane model. The geodesic is oriented such that it goes
        towards from ``real`` to the point at infinity.

        Use the ``-`` operator to pass to the geodesic with opposite
        orientation.
        """
        raise NotImplementedError

    def chord(self, a, b):
        r"""
        Return the geodesic from the point on the unit circle whose argument is
        `a` to the point whose argument is `b` in the Klein model.

        Both `a` and `b` are understood as rational multiples of 2π, i.e., they
        are taken mod 1.
        """
        raise NotImplementedError

    def half_space(self, geodesic):
        r"""
        Return the closed half plane that is on the left of ``geodesic``.

        Use the ``-`` operator to pass to the half plane on the right.
        """
        raise NotImplementedError

    def intersection(self, subsets):
        r"""
        Return the intersection of convex ``subsets``.
        """
        raise NotImplementedError

    def _repr_(self):
        r"""
        Return a printable representation of this hyperbolic plane.

        EXAMPLES::

            sage: from flatsurf.geometry.hyperbolic import HyperbolicPlane
            sage: HyperbolicPlane(AA)
            Hyperbolic Plane over Algebraic Real Field

        """
        return f"Hyperbolic Plane over {repr(self.base_ring())}"


class HyperbolicConvexSubset(Element):
    r"""
    Base class for convex subsets of :class:`HyperbolicPlane`.
    """

    def _equations(self, model):
        r"""
        Return equations defining a set of half spaces such that this set is the intersection of these half spaces.

        The equations are given as triples ``a``, ``b``, ``c`` such that

        - if ``model`` is ``"half_plane"``, a point `x + iy` of the upper half
          plane is in the half space if `a(x^2 + y^2) + bx + c ≥ 0`.

        - if ``model`` is ``"klein"``, points `(x, y)` in the unit disk satisfy
          `a + bx + cy ≥ 0`.

        Note that the output is not unique since the coefficients can be scaled
        by a positive scalar.
        """
        raise NotImplementedError("Convex sets must implement this method.")

    def is_subset(self, other):
        r"""
        Return whether the convex set ``other`` is a subset of this set.
        """
        raise NotImplementedError

    def intersection(self, other):
        r"""
        Return the intersection with the ``other`` convex set.
        """
        return self.parent().intersection([self, other])

    def __contains__(self, point):
        r"""
        Return whether ``point`` is contained in this set.
        """
        raise NotImplementedError

    def is_finite(self):
        r"""
        Return whether all points in this set are finite.
        """
        raise NotImplementedError


class HyperbolicHalfSpace(HyperbolicConvexSubset):
    r"""
    A closed half space of the hyperbolic plane.

    Use :meth:`HyperbolicPlane.half_space` to create a half plane.
    """

    def __init__(self, geodesic):
        self._geodesic = geodesic

    def _neg_(self):
        raise NotImplementedError


class HyperbolicGeodesic(HyperbolicConvexSubset):
    r"""
    An oriented geodesic in the hyperbolic plane.

    Internally, we represent geodesics as the chords satisfying the equation `a
    + bx + cy=0` in the unit disc of the Klein model.

    The geodesic is oriented such that the half space `a + bx + cy ≥ 0` is on
    its left.
    """

    def __init__(self, parent, a, b, c):
        raise NotImplementedError

    def start(self):
        r"""
        Return the ideal starting point of this geodesic.

        Note that this is only possible if the radius of this geodesic is a
        square in the base ring of the :class:`HyperbolicPlane`.
        """
        raise NotImplementedError

    def end(self):
        r"""
        Return the ideal end point of this geodesic.

        Note that this is only possible if the radius of this geodesic is a
        square in the base ring of the :class:`HyperbolicPlane`.
        """
        return (-self).start()

    def _richcmp_(self, other, op):
        r"""
        Return how this geodesic compares to ``other``.

        Geodesics are partially ordered by their slope in the Klein model.
        """

    def _neg_(self):
        raise NotImplementedError

    def equation(self, model):
        r"""
        Return an equation for this geodesic as a triple ``a``, ``b``, ``c`` such that:

        - if ``model`` is ``"half_plane"``, a point `x + iy` of the upper half
          plane is on the geodesic if it satisfies `a(x^2 + y^2) + bx + c = 0`.
          The coefficients are such that the half plane `a(x^2 + y^2) + bx + c
          ≥ 0` is on the left of the geodesic.

        - if ``model`` is ``"klein"``, points `(x, y)` in the unit disk satisfy
          `a + bx + cy = 0`. The sign of the coefficients is such that the half
          plane `a + bx + cy ≥ 0` is on the left of the geodesic.

        Note that the output is not unique since the coefficients can be scaled
        by a positive scalar.
        """
        raise NotImplementedError


class HyperbolicPoint(HyperbolicConvexSubset):
    r"""
    A (possibly infinite) point in the :class:`HyperbolicPlane`.

    Internally, we represent a point as the Euclidean coordinates in the unit
    disc of the Klein model.
    """

    def __init__(self, parent, x, y):
        raise NotImplementedError

    def coordinates(self, model="half_plane", ring=None):
        r"""
        Return coordinates of this point in ``ring``.

        If ``model`` is ``"half_plane"``, return projective coordinates in the
        Poincaré half plane model.

        If ``model`` is ``"klein"``, return Euclidean coordinates in the Klein model.

        If no ``ring`` has been specified, an appropriate extension of the base
        ring of the :class:`HyperbolicPlane` is chosen where these coordinates
        live.
        """
        raise NotImplementedError


class HyperbolicConvexPolygon(HyperbolicConvexSubset):
    r"""
    A (possibly unbounded) closed polygon in the :class:`HyperbolicPlane`,
    i.e., the intersection of a finite number of :class:`HyperbolicHalfPlane`s.
    """

    def __init__(self, parent, half_planes, assume_normalized=False):
        raise NotImplementedError

    def _normalize(self):
        r"""
        Normalize the internal list of half planes so that they describe the
        :meth:`boundary`.
        """
        raise NotImplementedError

    def equations(self):
        r"""
        Return the equations describing the boundary of this polygon.

        The output is minimal and sorted by slope in the Klein model.
        """
        raise NotImplementedError

    def edges(self):
        r"""
        Return the :class:`HyperbolicEdge`s defining this polygon.
        """
        raise NotImplementedError

    def vertices(self):
        r"""
        Return the vertices of this polygon, i.e., the end points of the
        :meth:`edges`.
        """
        raise NotImplementedError


class HyperbolicEdge(HyperbolicConvexSubset):
    r"""
    An oriented (possibly infinite) segment in the hyperbolic plane such as a
    boundary edge of a :class:`HyperbolicConvexPolygon`.
    """

    def __init__(self, geodesic, start=None, end=None):
        raise NotImplementedError


class HyperbolicEmptySet(HyperbolicConvexSubset):
    r"""
    The empty subset of the hyperbolic plane.
    """

    def __init__(self, parent):
        raise NotImplementedError
