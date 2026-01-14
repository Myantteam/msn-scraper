import requests
import json
import csv
from typing import List, Dict, Optional
import time
import re
from urllib.parse import urlparse, unquote

class MSNDataFetcher:
    def __init__(self, provider_id: str = None):
        self.base_url = "https://assets.msn.com/service/news/feed/pages/fullchannelpage"
        self.provider_id = provider_id or "vid-nx9xwm4ac8jkgyp2qymus852ntch6haq5b8msw39hdgsf4anjjxa"
        
        self.headers = {
            "accept": "*/*",
            "origin": "https://www.msn.com",
            "referer": "https://www.msn.com/",
            "user-agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/143.0.0.0 Safari/537.36"
            ),
            "accept-language": "en-US,en;q=0.9"
        }
        self.base_params = {
            "ProviderId": self.provider_id,
            "activityId": "6967204a-2efc-4065-af18-1c4b8a469e6c",
            "apikey": "0QfOX3Vn51YCzitbLaRkTTBadtWpgTN8NZLW0C1SEM",
            "cm": "en-us",
            "it": "web",
            "memory": "8",
            "scn": "ANON",
            "timeOut": "2000",
            "user": "m-03EC584A9ABD66EE193F4E869B326772"
        }
        self.first_page_cache = None  # Cache for the first page
    
    @staticmethod
    def extract_provider_id_from_url(url: str) -> Optional[str]:
        """
        Extract provider ID from MSN channel URL
        Example: https://www.msn.com/en-us/channel/source/FinanceBuzz%20Money/sr-vid-nx9xwm4ac8jkgyp2qymus852ntch6haq5b8msw39hdgsf4anjjxa
        Returns: vid-nx9xwm4ac8jkgyp2qymus852ntch6haq5b8msw39hdgsf4anjjxa
        """
        # Look for sr-<provider_id> pattern in URL
        match = re.search(r'/sr-(vid-[a-z0-9]+)', url)
        if match:
            return match.group(1)
        
        # Alternative: look for the pattern at the end of path
        match = re.search(r'/(vid-[a-z0-9]+)/?$', url)
        if match:
            return match.group(1)
        
        return None
    
    @staticmethod
    def extract_provider_name_from_url(url: str) -> Optional[str]:
        """
        Extract provider name from MSN channel URL
        Example: https://www.msn.com/en-us/channel/source/FinanceBuzz%20Money/sr-vid-...
        Returns: FinanceBuzz Money
        """
        # Look for pattern: /source/<provider_name>/sr-
        match = re.search(r'/source/([^/]+)/sr-', url)
        if match:
            provider_name = unquote(match.group(1))
            # Clean up the name for use in filenames
            provider_name = provider_name.replace('%20', ' ')
            return provider_name
        
        return None
    
    @staticmethod
    def sanitize_filename(name: str) -> str:
        """
        Convert provider name to a safe filename
        Example: "FinanceBuzz Money" -> "FinanceBuzz_Money"
        """
        # Replace spaces and special characters with underscores
        safe_name = re.sub(r'[^a-zA-Z0-9]+', '_', name)
        # Remove leading/trailing underscores
        safe_name = safe_name.strip('_')
        return safe_name
        
    def extract_post_data(self, card: Dict, provider_filter: bool = True) -> Optional[Dict]:
        """Extract relevant data from a post card"""
        # Skip if not an article or slideshow
        if card.get("type") not in ["article", "slideshow"]:
            return None
        
        # Filter by provider if requested
        if provider_filter:
            provider = card.get("provider", {})
            provider_profile_id = provider.get("profileId", "")
            
            # Only accept posts from the channel's provider
            if provider_profile_id != self.provider_id:
                return None
            
        # Extract reaction counts
        reaction_summary = card.get("reactionSummary", {})
        total_reactions = reaction_summary.get("totalCount", 0)
        
        likes = 0
        dislikes = 0
        for sub_reaction in reaction_summary.get("subReactionSummaries", []):
            if sub_reaction.get("type") == "upvote":
                likes = sub_reaction.get("totalCount", 0)
            elif sub_reaction.get("type") == "downvote":
                dislikes = sub_reaction.get("totalCount", 0)
        
        # Extract comment count
        comment_summary = card.get("commentSummary", {})
        total_comments = comment_summary.get("totalCount", 0)
        
        return {
            "id": card.get("id", ""),
            "title": card.get("title", ""),
            "type": card.get("type", ""),
            "url": card.get("url", ""),
            "likes": likes,
            "dislikes": dislikes,
            "total_reactions": total_reactions,
            "total_comments": total_comments,
            "published_date": card.get("publishedDateTime", ""),
            "provider": card.get("provider", {}).get("name", ""),
            "provider_id": card.get("provider", {}).get("profileId", ""),
            "abstract": card.get("abstract", "")
        }
    
    def get_channel_metadata(self, data: Dict) -> Dict:
        """Extract channel metadata including total post counts"""
        metadata = {
            "total_sections": 0,
            "total_cards_in_response": 0,
            "provider_feed_posts": 0,
            "other_posts": 0,
            "next_page_available": False
        }
        
        # Count sections and cards
        sections = data.get("sections", [])
        metadata["total_sections"] = len(sections)
        
        total_cards = 0
        for section in sections:
            cards = section.get("cards", [])
            total_cards += len(cards)
            
            # Count subcards in ProviderFeed specifically
            for card in cards:
                if card.get("type") == "ProviderFeed":
                    metadata["provider_feed_posts"] = card.get("subCardsCount", 0)
                elif card.get("type") == "TopicFeed":
                    metadata["other_posts"] = card.get("subCardsCount", 0)
        
        metadata["total_cards_in_response"] = total_cards
        
        # Check if there's a next page
        metadata["next_page_available"] = bool(data.get("nextPageUrl"))
        
        return metadata
    
    def fetch_page(self, next_page_url: Optional[str] = None, use_cache: bool = True) -> Dict:
        """Fetch a single page of data"""
        # Use cached first page if available and requested
        if use_cache and next_page_url is None and self.first_page_cache is not None:
            print("  → Using cached first page")
            return self.first_page_cache
        
        if next_page_url:
            response = requests.get(next_page_url, headers=self.headers, timeout=10)
        else:
            response = requests.get(
                self.base_url, 
                params=self.base_params, 
                headers=self.headers, 
                timeout=10
            )
        
        response.raise_for_status()
        data = response.json()
        
        # Cache the first page
        if next_page_url is None and self.first_page_cache is None:
            self.first_page_cache = data
        
        return data
    
    def extract_posts_from_page(self, data: Dict, provider_filter: bool = True) -> List[Dict]:
        """
        Extract posts from a page response
        
        Args:
            data: Page response data
            provider_filter: If True, only include posts from the channel's provider
        """
        posts = []
        
        sections = data.get("sections", [])
        for section in sections:
            cards = section.get("cards", [])
            for card in cards:
                # Focus on ProviderFeed which contains the channel's posts
                if card.get("type") == "ProviderFeed" and "subCards" in card:
                    for sub_card in card.get("subCards", []):
                        post_data = self.extract_post_data(sub_card, provider_filter)
                        if post_data:
                            posts.append(post_data)
                # Also check top-level articles (just in case)
                elif card.get("type") in ["article", "slideshow"]:
                    post_data = self.extract_post_data(card, provider_filter)
                    if post_data:
                        posts.append(post_data)
        
        return posts
    
    def get_next_page_url(self, data: Dict) -> Optional[str]:
        """Extract the next page URL from response"""
        return data.get("nextPageUrl")
    
    def estimate_total_posts(self, provider_filter: bool = True) -> Dict:
        """
        Fetch first page to estimate total available posts
        
        Returns:
            Dictionary with estimation information
        """
        print("Fetching first page to analyze channel...")
        
        try:
            data = self.fetch_page()  # This will cache the first page
            metadata = self.get_channel_metadata(data)
            posts_on_first_page = len(self.extract_posts_from_page(data, provider_filter))
            
            estimation = {
                "posts_on_first_page": posts_on_first_page,
                "provider_feed_posts": metadata["provider_feed_posts"],
                "other_posts": metadata["other_posts"],
                "has_pagination": metadata["next_page_available"],
                "metadata": metadata
            }
            
            # Try to parse the nextPageUrl to see skip parameters
            next_url = data.get("nextPageUrl", "")
            if "skip" in next_url or "newsSkip" in next_url:
                # Extract skip value from URL
                import re
                skip_match = re.search(r'skip=(\d+)', next_url)
                if skip_match:
                    estimation["skip_increment"] = int(skip_match.group(1))
            
            return estimation
            
        except Exception as e:
            print(f"Error estimating total posts: {e}")
            return {}
    
    def fetch_posts(self, max_posts: int = 50, delay: float = 1.0, 
                    show_estimation: bool = True, provider_filter: bool = True,
                    save_incrementally: bool = False, csv_filename: str = "msn_posts.csv",
                    json_filename: str = "msn_posts.json") -> List[Dict]:
        """
        Fetch posts up to max_posts limit
        
        Args:
            max_posts: Maximum number of posts to fetch (None for all posts)
            delay: Delay in seconds between requests (to be respectful)
            show_estimation: Whether to show channel estimation before fetching
            provider_filter: If True, only include posts from the channel's provider
            save_incrementally: If True, save after each page fetch
            csv_filename: CSV file name for incremental saving
            json_filename: JSON file name for incremental saving
        
        Returns:
            List of post dictionaries
        """
        # Show estimation if requested
        if show_estimation:
            print("="*60)
            print("CHANNEL ANALYSIS")
            print("="*60)
            
            estimation = self.estimate_total_posts(provider_filter)
            if estimation:
                print(f"\nProvider feed posts on first page: {estimation['provider_feed_posts']}")
                print(f"Other posts (TopicFeed/suggestions): {estimation['other_posts']}")
                print(f"Filtered posts (channel only): {estimation['posts_on_first_page']}")
                print(f"Pagination available: {estimation['has_pagination']}")
                if estimation.get('skip_increment'):
                    print(f"Skip increment: {estimation['skip_increment']}")
                print(f"\n{'Filter mode: ' + ('CHANNEL POSTS ONLY' if provider_filter else 'ALL POSTS')}")
                print("You can fetch all available posts or set a limit.\n")
        
        all_posts = []
        next_page_url = None
        page_count = 0
        
        # Initialize CSV file if saving incrementally
        if save_incrementally:
            fieldnames = [
                "id", "title", "type", "url", "likes", "dislikes", 
                "total_reactions", "total_comments", "published_date", 
                "provider", "provider_id", "abstract"
            ]
            csv_file = open(csv_filename, "w", newline="", encoding="utf-8")
            csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            csv_writer.writeheader()
        
        print("="*60)
        print(f"FETCHING POSTS (Limit: {'ALL' if max_posts is None else max_posts})")
        print("="*60)
        print(f"Starting to fetch {'all available' if max_posts is None else f'up to {max_posts}'} posts...\n")
        
        while max_posts is None or len(all_posts) < max_posts:
            page_count += 1
            print(f"Fetching page {page_count}...")
            
            try:
                # Fetch page (will use cache for first page)
                data = self.fetch_page(next_page_url)
                
                # Show metadata for first page
                if page_count == 1:
                    metadata = self.get_channel_metadata(data)
                    print(f"  → Sections in response: {metadata['total_sections']}")
                    print(f"  → Provider feed posts: {metadata['provider_feed_posts']}")
                    print(f"  → Other posts: {metadata['other_posts']}")
                
                # Extract posts
                posts = self.extract_posts_from_page(data, provider_filter)
                print(f"  → Found {len(posts)} channel posts on this page")
                
                # Add posts (respecting max_posts limit if set)
                if max_posts is None:
                    posts_to_add = posts
                else:
                    remaining_slots = max_posts - len(all_posts)
                    posts_to_add = posts[:remaining_slots]
                
                all_posts.extend(posts_to_add)
                
                # Save incrementally if enabled
                if save_incrementally and posts_to_add:
                    csv_writer.writerows(posts_to_add)
                    csv_file.flush()  # Ensure data is written to disk
                    print(f"  → Saved {len(posts_to_add)} posts to {csv_filename}")
                
                print(f"  → Total posts collected: {len(all_posts)}{'' if max_posts is None else f'/{max_posts}'}")
                
                # Check if we've reached the limit
                if max_posts is not None and len(all_posts) >= max_posts:
                    print("\n✓ Reached maximum post limit!")
                    break
                
                # Get next page URL
                next_page_url = self.get_next_page_url(data)
                
                if not next_page_url:
                    print("\n✓ No more pages available!")
                    break
                
                # Be respectful - add delay between requests (but not after last page)
                if next_page_url:
                    time.sleep(delay)
                
            except Exception as e:
                print(f"✗ Error fetching page {page_count}: {e}")
                break
        
        # Close CSV file if saving incrementally
        if save_incrementally:
            csv_file.close()
            print(f"\n✓ CSV file saved: {csv_filename}")
            
            # Also save JSON at the end
            self.save_to_json(all_posts, json_filename)
        
        return all_posts
    
    def save_to_csv(self, posts: List[Dict], filename: str = "msn_posts.csv"):
        """Save posts to CSV file"""
        if not posts:
            print("No posts to save!")
            return
        
        fieldnames = [
            "id", "title", "type", "url", "likes", "dislikes", 
            "total_reactions", "total_comments", "published_date", 
            "provider", "provider_id", "abstract"
        ]
        
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(posts)
        
        print(f"\n✓ Data saved to {filename}")
    
    def save_to_json(self, posts: List[Dict], filename: str = "msn_posts.json"):
        """Save posts to JSON file"""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Data saved to {filename}")


def main():
    print("="*60)
    print("MSN CHANNEL POST SCRAPER")
    print("="*60)
    
    # Ask for MSN channel URL
    print("\nPlease enter the MSN channel URL:")
    print("Example: https://www.msn.com/en-us/channel/source/FinanceBuzz%20Money/sr-vid-nx9xwm4ac8jkgyp2qymus852ntch6haq5b8msw39hdgsf4anjjxa")
    
    channel_url = input("\nURL: ").strip()
    
    # Extract provider ID from URL
    provider_id = MSNDataFetcher.extract_provider_id_from_url(channel_url)
    
    if not provider_id:
        print("\n✗ Could not extract provider ID from URL!")
        print("Please make sure the URL contains the provider ID (e.g., sr-vid-...)")
        return
    
    print(f"\n✓ Extracted Provider ID: {provider_id}")
    
    # Extract provider name from URL
    provider_name = MSNDataFetcher.extract_provider_name_from_url(channel_url)
    if provider_name:
        print(f"✓ Extracted Provider Name: {provider_name}")
        safe_name = MSNDataFetcher.sanitize_filename(provider_name)
        csv_filename = f"{safe_name}_posts.csv"
        json_filename = f"{safe_name}_posts.json"
    else:
        print("⚠ Could not extract provider name, using default filenames")
        csv_filename = "msn_posts.csv"
        json_filename = "msn_posts.json"
    
    print(f"\nFiles will be saved as:")
    print(f"  - {csv_filename}")
    print(f"  - {json_filename}")
    
    # Initialize fetcher
    fetcher = MSNDataFetcher(provider_id=provider_id)
    
    # Ask how many posts to scrape
    print("\n" + "="*60)
    print("How many posts do you want to scrape?")
    print("  - Enter a number (e.g., 50, 100, 200)")
    print("  - Enter 'all' to fetch all available posts")
    
    while True:
        user_input = input("\nNumber of posts (or 'all'): ").strip().lower()
        
        if user_input == 'all':
            MAX_POSTS = None
            print("\n✓ Will fetch ALL available posts")
            break
        elif user_input.isdigit():
            MAX_POSTS = int(user_input)
            print(f"\n✓ Will fetch up to {MAX_POSTS} posts")
            break
        else:
            print("✗ Invalid input. Please enter a number or 'all'")
    
    # Fetch posts with incremental saving
    posts = fetcher.fetch_posts(
        max_posts=MAX_POSTS, 
        delay=1.0, 
        show_estimation=True,
        provider_filter=True,
        save_incrementally=True,
        csv_filename=csv_filename,
        json_filename=json_filename
    )
    
    # Display summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Total posts fetched: {len(posts)}")
    
    if posts:
        # Check if all posts are from the same provider
        providers = set(p["provider"] for p in posts)
        print(f"Providers in results: {', '.join(providers)}")
        
        total_likes = sum(p["likes"] for p in posts)
        total_dislikes = sum(p["dislikes"] for p in posts)
        total_comments = sum(p["total_comments"] for p in posts)
        
        print(f"Total likes: {total_likes}")
        print(f"Total dislikes: {total_dislikes}")
        print(f"Total comments: {total_comments}")
        
        # Display first few posts
        print(f"\n{'='*60}")
        print("SAMPLE POSTS:")
        print(f"{'='*60}")
        for i, post in enumerate(posts[:5], 1):
            print(f"\n{i}. {post['title'][:80]}...")
            print(f"   👍 {post['likes']} | 👎 {post['dislikes']} | 💬 {post['total_comments']}")
            print(f"   Provider: {post['provider']}")
    
    print(f"\n✓ All data has been saved!")


if __name__ == "__main__":
    main()