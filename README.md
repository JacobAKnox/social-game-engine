# social-game-engine
A social game engine for games made to be played over discord. Made as a personal project starting in Nov 2022

The core of the engine is the ECS that someone can use to implement their own game logic. The system is my own design. It uses a component class that can be subclassed to store structured data. The entities are just a collection of components in the world class that can be queried by uuid or component set. Functions can be defined as processors by taking a world argument, *args, and **kwargs. There are a few decorators that make querying and looping over entities simpler. The design of components allows the engine to handle serialization and deserialization of the game state.

There is an event handler based on the one in esper[https://github.com/benmoran56/esper], but modified to better suit my needs. Any function can passed as a event handler and the events are strings so they can be expanded on by the user.

The UI module uses nextcord[https://github.com/nextcord/nextcord] to create a bot and provides and interface for interacting with players. This is currently a work in progress. It is being developed in parallel with the the mafia implementation.

The Mafia module is a work in progress implementation of the game mafia. It is a good example of how to use the engine.

The current implementation of storage uses mongodb through pymongo. It is fully functional, but I would like to move to a solution where the game state can be queried from the database rather than loading everything on startup. The current implementation was built to make testing and development easier, but it does not scale and a new system would better support multiple games on one bot.

The tests module contains a suite of automated tests to enable a CI approach to development and ensure that the engine is working as expected. Because I am the only person working on it, all tests are run on my machine before pushing to github. I would like to move to a CI system in the future.
