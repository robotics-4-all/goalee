from __future__ import annotations

import pytest

from goalee.types import Orientation, Point, Pose

# --- Point ---


class TestPointSub:
    def test_sub_point(self):
        p1 = Point(5.0, 7.0, 9.0)
        p2 = Point(1.0, 2.0, 3.0)
        result = p1 - p2
        assert result == Point(4.0, 5.0, 6.0)

    def test_sub_float(self):
        p = Point(5.0, 7.0, 9.0)
        result = p - 1.0
        assert result == Point(4.0, 6.0, 8.0)

    def test_sub_int(self):
        p = Point(5.0, 7.0, 9.0)
        result = p - 1
        assert result == Point(4.0, 6.0, 8.0)

    def test_sub_invalid_raises(self):
        p = Point(1.0, 2.0, 3.0)
        with pytest.raises(ValueError):
            p - "invalid"


class TestPointEq:
    def test_eq_point_true(self):
        assert Point(1.0, 2.0, 3.0) == Point(1.0, 2.0, 3.0)

    def test_eq_point_false(self):
        assert Point(1.0, 2.0, 3.0) != Point(4.0, 5.0, 6.0)

    def test_eq_dict_true(self):
        p = Point(1.0, 2.0, 3.0)
        assert p == {"x": 1.0, "y": 2.0, "z": 3.0}

    def test_eq_dict_false(self):
        p = Point(1.0, 2.0, 3.0)
        assert p != {"x": 9.0, "y": 9.0, "z": 9.0}

    def test_eq_other_returns_false(self):
        p = Point(1.0, 2.0, 3.0)
        assert (p == "string") is False
        assert (p == 42) is False


class TestPointComparisons:
    def test_lt_point(self):
        assert Point(1.0, 2.0, 3.0) < Point(2.0, 2.0, 3.0)
        assert not (Point(2.0, 2.0, 3.0) < Point(1.0, 2.0, 3.0))

    def test_lt_dict(self):
        assert Point(1.0, 2.0, 3.0) < {"x": 2.0, "y": 2.0, "z": 3.0}

    def test_lt_unsupported(self):
        assert Point(1.0, 2.0, 3.0).__lt__("bad") is NotImplemented

    def test_le_point(self):
        assert Point(1.0, 2.0, 3.0) <= Point(1.0, 2.0, 3.0)
        assert Point(1.0, 2.0, 3.0) <= Point(2.0, 2.0, 3.0)

    def test_le_dict(self):
        assert Point(1.0, 2.0, 3.0) <= {"x": 1.0, "y": 2.0, "z": 3.0}

    def test_le_unsupported(self):
        assert Point(1.0, 2.0, 3.0).__le__("bad") is NotImplemented

    def test_gt_point(self):
        assert Point(2.0, 2.0, 3.0) > Point(1.0, 2.0, 3.0)
        assert not (Point(1.0, 2.0, 3.0) > Point(2.0, 2.0, 3.0))

    def test_gt_dict(self):
        assert Point(2.0, 2.0, 3.0) > {"x": 1.0, "y": 2.0, "z": 3.0}

    def test_gt_unsupported(self):
        assert Point(1.0, 2.0, 3.0).__gt__("bad") is NotImplemented

    def test_ge_point(self):
        assert Point(1.0, 2.0, 3.0) >= Point(1.0, 2.0, 3.0)
        assert Point(2.0, 2.0, 3.0) >= Point(1.0, 2.0, 3.0)

    def test_ge_dict(self):
        assert Point(1.0, 2.0, 3.0) >= {"x": 1.0, "y": 2.0, "z": 3.0}

    def test_ge_unsupported(self):
        assert Point(1.0, 2.0, 3.0).__ge__("bad") is NotImplemented


class TestPointAbs:
    def test_abs_known_values(self):
        p = Point(3.0, 4.0, 0.0)
        assert p.abs() == 5.0

    def test_abs_origin(self):
        p = Point(0.0, 0.0, 0.0)
        assert p.abs() == 0.0

    def test_abs_3d(self):
        p = Point(1.0, 2.0, 2.0)
        assert p.abs() == 3.0


class TestPointAdd:
    def test_add_point(self):
        result = Point(1.0, 2.0, 3.0) + Point(4.0, 5.0, 6.0)
        assert result == Point(5.0, 7.0, 9.0)

    def test_add_float(self):
        result = Point(1.0, 2.0, 3.0) + 10.0
        assert result == Point(11.0, 12.0, 13.0)

    def test_add_int(self):
        result = Point(1.0, 2.0, 3.0) + 10
        assert result == Point(11.0, 12.0, 13.0)

    def test_add_invalid_raises(self):
        with pytest.raises(ValueError):
            Point(1.0, 2.0, 3.0) + "invalid"


class TestPointDefaults:
    def test_defaults(self):
        p = Point()
        assert p.x == 0.0
        assert p.y == 0.0
        assert p.z == 0.0


# --- Orientation ---


class TestOrientationSub:
    def test_sub_orientation(self):
        o1 = Orientation(0.5, 0.7, 0.9)
        o2 = Orientation(0.1, 0.2, 0.3)
        result = o1 - o2
        assert abs(result.roll - 0.4) < 1e-9
        assert abs(result.pitch - 0.5) < 1e-9
        assert abs(result.yaw - 0.6) < 1e-9

    def test_sub_float(self):
        o = Orientation(1.0, 2.0, 3.0)
        result = o - 0.5
        assert abs(result.roll - 0.5) < 1e-9
        assert abs(result.pitch - 1.5) < 1e-9
        assert abs(result.yaw - 2.5) < 1e-9

    def test_sub_int(self):
        o = Orientation(1.0, 2.0, 3.0)
        result = o - 1
        assert abs(result.roll - 0.0) < 1e-9

    def test_sub_invalid_raises(self):
        with pytest.raises(ValueError):
            Orientation(1.0, 2.0, 3.0) - "invalid"


class TestOrientationEq:
    def test_eq_orientation_true(self):
        assert Orientation(0.1, 0.2, 0.3) == Orientation(0.1, 0.2, 0.3)

    def test_eq_orientation_false(self):
        assert Orientation(0.1, 0.2, 0.3) != Orientation(0.4, 0.5, 0.6)

    def test_eq_dict_true(self):
        o = Orientation(0.1, 0.2, 0.3)
        assert o == {"roll": 0.1, "pitch": 0.2, "yaw": 0.3}

    def test_eq_dict_false(self):
        o = Orientation(0.1, 0.2, 0.3)
        assert o != {"roll": 9.0, "pitch": 9.0, "yaw": 9.0}

    def test_eq_other_returns_false(self):
        o = Orientation(0.1, 0.2, 0.3)
        assert (o == "string") is False
        assert (o == 42) is False


class TestOrientationAbs:
    def test_abs_known(self):
        o = Orientation(1.0, 2.0, 2.0)
        assert o.abs() == 3.0

    def test_abs_zero(self):
        o = Orientation(0.0, 0.0, 0.0)
        assert o.abs() == 0.0


class TestOrientationAdd:
    def test_add_orientation(self):
        result = Orientation(0.1, 0.2, 0.3) + Orientation(0.4, 0.5, 0.6)
        assert abs(result.roll - 0.5) < 1e-9
        assert abs(result.pitch - 0.7) < 1e-9
        assert abs(result.yaw - 0.9) < 1e-9

    def test_add_float(self):
        result = Orientation(0.1, 0.2, 0.3) + 1.0
        assert abs(result.roll - 1.1) < 1e-9
        assert abs(result.pitch - 1.2) < 1e-9
        assert abs(result.yaw - 1.3) < 1e-9

    def test_add_int(self):
        result = Orientation(0.1, 0.2, 0.3) + 1
        assert abs(result.roll - 1.1) < 1e-9

    def test_add_invalid_raises(self):
        with pytest.raises(ValueError):
            Orientation(0.1, 0.2, 0.3) + "invalid"


class TestOrientationComparisons:
    def test_gt_orientation(self):
        assert Orientation(1.0, 0.0, 0.0) > Orientation(0.0, 0.0, 0.0)
        assert not (Orientation(0.0, 0.0, 0.0) > Orientation(1.0, 0.0, 0.0))

    def test_gt_dict(self):
        assert Orientation(1.0, 0.0, 0.0) > {"roll": 0.0, "pitch": 0.0, "yaw": 0.0}

    def test_gt_unsupported(self):
        assert Orientation(1.0, 0.0, 0.0).__gt__("bad") is NotImplemented

    def test_ge_orientation(self):
        assert Orientation(1.0, 0.0, 0.0) >= Orientation(1.0, 0.0, 0.0)
        assert Orientation(1.0, 0.0, 0.0) >= Orientation(0.0, 0.0, 0.0)

    def test_ge_dict(self):
        assert Orientation(1.0, 0.0, 0.0) >= {"roll": 1.0, "pitch": 0.0, "yaw": 0.0}

    def test_ge_unsupported(self):
        assert Orientation(1.0, 0.0, 0.0).__ge__("bad") is NotImplemented

    def test_lt_orientation(self):
        assert Orientation(0.0, 0.0, 0.0) < Orientation(1.0, 0.0, 0.0)
        assert not (Orientation(1.0, 0.0, 0.0) < Orientation(0.0, 0.0, 0.0))

    def test_lt_dict(self):
        assert Orientation(0.0, 0.0, 0.0) < {"roll": 1.0, "pitch": 0.0, "yaw": 0.0}

    def test_lt_unsupported(self):
        assert Orientation(0.0, 0.0, 0.0).__lt__("bad") is NotImplemented

    def test_le_orientation(self):
        assert Orientation(0.0, 0.0, 0.0) <= Orientation(0.0, 0.0, 0.0)
        assert Orientation(0.0, 0.0, 0.0) <= Orientation(1.0, 0.0, 0.0)

    def test_le_dict(self):
        assert Orientation(0.0, 0.0, 0.0) <= {"roll": 0.0, "pitch": 0.0, "yaw": 0.0}

    def test_le_unsupported(self):
        # Orientation.__le__ with dict is the last branch — no return NotImplemented
        # The source code has no return for unsupported in __le__, so it returns None
        result = Orientation(0.0, 0.0, 0.0).__le__("bad")
        assert result is None


class TestOrientationXYZAliases:
    def test_xyz_alias_single(self):
        o = Orientation(z=1.5)
        assert o.yaw == 1.5
        assert o.roll == 0.0
        assert o.pitch == 0.0

    def test_xyz_alias_all(self):
        o = Orientation(x=0.1, y=0.2, z=0.3)
        assert o.roll == 0.1
        assert o.pitch == 0.2
        assert o.yaw == 0.3

    def test_roll_pitch_yaw_still_work(self):
        o = Orientation(roll=0.1, pitch=0.2, yaw=0.3)
        assert o.roll == 0.1
        assert o.pitch == 0.2
        assert o.yaw == 0.3

    def test_explicit_roll_pitch_yaw_takes_precedence(self):
        o = Orientation(roll=0.5, x=0.9)
        assert o.roll == 0.5

    def test_positional_args_still_work(self):
        o = Orientation(0.1, 0.2, 0.3)
        assert o.roll == 0.1
        assert o.pitch == 0.2
        assert o.yaw == 0.3


class TestOrientationDefaults:
    def test_defaults(self):
        o = Orientation()
        assert o.roll == 0.0
        assert o.pitch == 0.0
        assert o.yaw == 0.0


# --- Pose ---


class TestPose:
    def test_creation(self):
        p = Point(1.0, 2.0, 3.0)
        o = Orientation(0.1, 0.2, 0.3)
        pose = Pose(translation=p, orientation=o)
        assert pose.translation == p
        assert pose.orientation == o

    def test_pose_fields(self):
        pose = Pose(translation=Point(), orientation=Orientation())
        assert pose.translation.x == 0.0
        assert pose.orientation.roll == 0.0
