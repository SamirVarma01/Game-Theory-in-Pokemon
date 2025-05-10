# src/python/main.py
import asyncio
import json
import aiohttp
import logging
from agent import GameTheoryAgent
from poke_env import AccountConfiguration, LocalhostServerConfiguration, RandomPlayer

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def send_update(message: str, is_win: bool = None):
    logger.debug(f"Sending update - Message: {message}, IsWin: {is_win}")
    async with aiohttp.ClientSession() as session:
        update = {
            "message": message,
            "isWin": is_win
        }
        try:
            async with session.post('http://localhost:5000', json=update) as response:
                if response.status != 200:
                    logger.error(f"Failed to send update: {response.status}")
                else:
                    logger.debug("Update sent successfully")
        except Exception as e:
            logger.error(f"Error sending update: {e}")

class BattleTrackingAgent(GameTheoryAgent):
    async def _handle_battle_message(self, split_messages):
        logger.debug(f"Received battle message: {split_messages}")
        await super()._handle_battle_message(split_messages)
        
        # Check for battle end messages
        for message in split_messages:
            if len(message) > 1:
                logger.debug(f"Processing message part: {message}")
                if message[1] == "win":
                    # Battle won
                    logger.info(f"Battle won against {message[2]}")
                    await send_update(f"Battle won against {message[2]}!", True)
                elif message[1] == "lose":
                    # Battle lost
                    logger.info(f"Battle lost against {message[2]}")
                    await send_update(f"Battle lost against {message[2]}!", False)
                elif message[1] == "tie":
                    # Battle tied
                    logger.info("Battle ended in a tie")
                    await send_update("Battle ended in a tie!", None)

async def main():
    logger.info("Starting battle simulation...")
    
    try:
        # Set up player configuration
        account_config = AccountConfiguration("GameTheoryBot", "")  # Empty password for local server
        
        # Create our agent with battle tracking
        player = BattleTrackingAgent(
            account_configuration=account_config,
            server_configuration=LocalhostServerConfiguration,
            battle_format="gen9randombattle"
        )
        
        # Create a random player for testing
        random_player = RandomPlayer(
            account_configuration=AccountConfiguration("RandomPlayer", ""),
            server_configuration=LocalhostServerConfiguration,
            battle_format="gen9randombattle"
        )

        # Send initial update
        logger.info("Sending initial update...")
        await send_update("Starting battle simulation...")

        # Play games
        logger.info("Starting battles...")
        try:
            # Add timeout for battles
            async with asyncio.timeout(600):  # 10 minutes timeout
                await player.battle_against(random_player, n_battles=5)
            logger.info("Battles completed successfully")
        except asyncio.TimeoutError:
            logger.error("Battles timed out after 10 minutes")
            await send_update("Battles timed out - check logs for details")
            raise
        except Exception as e:
            logger.error(f"Error during battles: {e}")
            await send_update(f"Error during battles: {str(e)}")
            raise

        # Send final update
        logger.info("Sending final update...")
        await send_update("Battle simulation completed!")
        logger.info("Battle simulation completed!")
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program interrupted by user")
    except Exception as e:
        logger.error(f"Program failed with error: {e}")
