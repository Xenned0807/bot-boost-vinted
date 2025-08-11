# vinted_client.py
import aiohttp
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class VintedClient:
    def __init__(self, search_url: str):
        if not search_url:
            raise ValueError("L'URL de recherche Vinted ne peut pas être vide.")
        self.search_url = search_url
        self.seen_item_ids = set()
        self.first_run = True
        self.session = None

    async def initialize_session(self):
        """Initialise la session aiohttp et obtient un cookie de session valide."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        self.session = aiohttp.ClientSession(headers=headers)
        
        # Visiter la page d'accueil pour obtenir les cookies nécessaires
        try:
            logging.info("Tentative d'obtention du cookie de session Vinted...")
            async with self.session.get("https://www.vinted.fr/") as response:
                response.raise_for_status()
                # Le cookie est maintenant stocké dans le "cookie_jar" de la session
                logging.info("Cookie de session obtenu avec succès.")
                return True
        except aiohttp.ClientError as e:
            logging.error(f"Impossible d'obtenir le cookie de session Vinted : {e}")
            await self.session.close() # Nettoyer la session en cas d'échec
            self.session = None
            return False

    async def search_new_items(self) -> list:
        if not self.session or self.session.closed:
            logging.error("La session n'est pas initialisée. Impossible de faire une recherche.")
            return []

        try:
            api_search_url = f"https://www.vinted.fr/api/v2/catalog/items?{self.search_url.split('?')[-1]}"
            async with self.session.get(api_search_url) as response:
                if response.status == 403:
                    logging.error("Erreur 403 Forbidden. Vinted bloque la requête. Il est possible que l'IP soit bannie ou que le cookie ait expiré.")
                    return []
                response.raise_for_status()
                data = await response.json()
                items = data.get("items", [])
                
                new_items = []
                current_item_ids = {item['id'] for item in items}

                if self.first_run:
                    self.seen_item_ids = current_item_ids
                    self.first_run = False
                    logging.info(f"Initialisation Vinted : {len(self.seen_item_ids)} articles actuels mémorisés.")
                else:
                    new_item_ids = current_item_ids - self.seen_item_ids
                    if new_item_ids:
                        new_items = [item for item in items if item['id'] in new_item_ids]
                        logging.info(f"Détection Vinted : {len(new_items)} nouveaux articles trouvés !")
                    self.seen_item_ids.update(new_item_ids)
                return new_items

        except aiohttp.ClientError as e:
            logging.error(f"Erreur API Vinted lors de la recherche : {e}")
            return []
        except Exception as e:
            logging.error(f"Erreur inattendue dans VintedClient : {e}")
            return []
            
    async def close_session(self):
        if self.session and not self.session.closed:
            await self.session.close()
