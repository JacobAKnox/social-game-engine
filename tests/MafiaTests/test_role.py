import logging
import unittest
from unittest.mock import AsyncMock

import Storage
import UI
from ECS import World
from Mafia import Guild
from Mafia.Channel import delete_player_role, PlayerRole, create_player_role

logging.disable(logging.CRITICAL)


class RoleTestCase(unittest.IsolatedAsyncioTestCase):

    def tearDown(self) -> None:
        Storage.clear_entity_collection()

    async def test_delete_role(self):
        world: World = World()
        UI.delete_role = AsyncMock()

        entity_id = world.add_components(None, Guild(123))

        await world.run_processor(delete_player_role, uuid=entity_id)

        UI.delete_role.assert_not_called()
        UI.delete_role.assert_not_awaited()

        entity_id = world.add_components(None, PlayerRole(456))

        await world.run_processor(delete_player_role, uuid=entity_id)

        UI.delete_role.assert_not_called()
        UI.delete_role.assert_not_awaited()

        entity_id = world.add_components(None, Guild(123), PlayerRole(456))

        await world.run_processor(delete_player_role, uuid=entity_id)

        UI.delete_role.assert_called_with(123, 456)

    async def test_make_role(self):
        world: World = World()
        UI.make_role = AsyncMock(return_value=456)

        entity_id = world.add_components(None)

        await world.run_processor(create_player_role, uuid=entity_id)

        UI.make_role.assert_not_called()
        self.assertTrue(PlayerRole not in world.get_components(entity_id, PlayerRole))

        entity_id = world.add_components(None, Guild(123))

        await world.run_processor(create_player_role, uuid=entity_id)

        UI.make_role.assert_called_with("player", 123)
        self.assertTrue(PlayerRole in world.get_components(entity_id, PlayerRole))
        self.assertEqual(world.get_components(entity_id, PlayerRole)[PlayerRole].data, 456)
