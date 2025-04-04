from typing import Any, List, Optional

from goalee.entity import Entity
from goalee.goal import Goal, GoalState
from goalee.types import Point


class WaypointTrajectoryGoal(Goal):
    def __init__(self,
                 entity: Entity,
                 waypoints: List[Point],
                 deviation: float = 0.0,
                 name: Optional[str] = None,
                 event_emitter: Optional[Any] = None,
                 max_duration: Optional[float] = None,
                 min_duration: Optional[float] = None):
        super().__init__([entity], event_emitter, name=name,
                         max_duration=max_duration,
                         min_duration=min_duration)
        self._entity = entity
        self._waypoints = waypoints
        self._deviation = deviation
        self._waypoints_reached_map = [False] * len(waypoints)

    def on_enter(self):
        self.log_debug(
            f'Starting PositionGoal <{self._name}> with params:\n'
            f'-> Entity: {self._entity.name}\n'
            f'-> Waypoints: {self._waypoints}\n'
            f'-> Deviation: {self._deviation}\n'
            f'-> Max Duration: {self._max_duration}\n'
            f'-> Min Duration: {self._min_duration}'
        )

    def current_target_waypoint(self):
        for i, reached in enumerate(self._waypoints_reached_map):
            if not reached:
                return self._waypoints[i], i

    def check_reached_waypoint(self):
        if self._last_state.get('position', None) is None:
            return
        pos = self._last_state['position']
        if pos.get('x', 'None') is None and pos.get('y', 'None') is None \
            and pos.get('z', 'None') is None:
                self.log_warning('Received invalid position values for x,y,z')
                return
        current_target, idx = self.current_target_waypoint()
        reached = (pos['x'] > (current_target.x - self._deviation) and \
                   pos['x'] < (current_target.x + self._deviation) and \
                   pos['y'] > (current_target.y - self._deviation) and \
                   pos['y'] < (current_target.y + self._deviation) and \
                   pos['z'] > (current_target.z - self._deviation) and \
                   pos['z'] < (current_target.z + self._deviation))
        if reached:
            self.log_info(f'Reached waypoint {idx}')
            self._waypoints_reached_map[idx] = True

    def tick(self):
        self._last_state = self._entity.attributes.copy()
        self.check_reached_waypoint()
        if all(self._waypoints_reached_map):
            self.set_state(GoalState.COMPLETED)
