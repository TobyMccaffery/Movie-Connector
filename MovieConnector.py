import requests
from collections import deque
import tkinter as tk
from tkinter import messagebox

API_KEY = "INSERT API KEY HERE"
TMDB_BASE_URL = "https://api.themoviedb.org/3"

#Cache actor's movie credits to minimise API calls
actor_movies_cache = {}

#Helper function to search for a movie by title
def search_movie(title):
    try:
        url = f"{TMDB_BASE_URL}/search/movie"
        params = {"api_key": API_KEY, "query": title}
        response = requests.get(url, params=params)
        response.raise_for_status()  # Check for request errors
        
        results = response.json().get('results', [])
        if results:
            return results[0]['id'], results[0]['title']
        return None, None
    except requests.exceptions.RequestException as e:
        print(f"API error while searching for movie '{title}': {e}")
        return None, None

#Helper function to get the cast of a movie
def get_movie_cast(movie_id):
    try:
        url = f"{TMDB_BASE_URL}/movie/{movie_id}/credits"
        params = {"api_key": API_KEY}
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get('cast', [])
    except requests.exceptions.RequestException as e:
        print(f"API error while fetching cast for movie ID {movie_id}: {e}")
        return []

#Helper function to get movies for a specific actor (with caching)
def get_actor_movies(actor_id):
    if actor_id in actor_movies_cache:
        return actor_movies_cache[actor_id]
    
    try:
        url = f"{TMDB_BASE_URL}/person/{actor_id}/movie_credits"
        params = {"api_key": API_KEY}
        response = requests.get(url, params=params)
        response.raise_for_status()
        actor_movies_cache[actor_id] = response.json().get('cast', [])
        return actor_movies_cache[actor_id]
    except requests.exceptions.RequestException as e:
        print(f"API error while fetching movies for actor ID {actor_id}: {e}")
        return []

#Optimised bidirectional search for shortest path between movies
def find_shortest_movie_path(start_movie_title, target_movie_title, status_label=None):
    start_movie_id, start_movie_name = search_movie(start_movie_title)
    target_movie_id, target_movie_name = search_movie(target_movie_title)

    if not start_movie_id:
        return f"Error: Could not find movie '{start_movie_title}'"
    if not target_movie_id:
        return f"Error: Could not find movie '{target_movie_title}'"

    if start_movie_id == target_movie_id:
        return f"Start and target movie are the same: '{start_movie_name}'"

    #Bidirectional BFS initialisation
    queue_start = deque([(start_movie_id, [start_movie_name])])
    queue_target = deque([(target_movie_id, [target_movie_name])])
    
    visited_start = {start_movie_id: [start_movie_name]}
    visited_target = {target_movie_id: [target_movie_name]}

    def bfs_step(queue, visited, other_visited):
        current_movie_id, path = queue.popleft()
        
        if status_label:
            status_label.config(text=f"Pruning: {path[-1]}")
            status_label.update()

        cast = get_movie_cast(current_movie_id)
        if not cast:
            return None

        for actor in cast:
            actor_id = actor['id']
            actor_name = actor['name']

            for movie in get_actor_movies(actor_id):
                movie_id = movie['id']
                movie_title = movie['title']

                # If the movie is in the other visited set, we found a connection
                if movie_id in other_visited:
                    return path + [f"{actor_name} -> {movie_title}"] + other_visited[movie_id][::-1]

                if movie_id not in visited:
                    visited[movie_id] = path + [f"{actor_name} -> {movie_title}"]
                    queue.append((movie_id, visited[movie_id]))

        return None

    #Perform bidirectional BFS until a connection is found
    while queue_start and queue_target:
        #Alternate BFS between the start and target sides
        result = bfs_step(queue_start, visited_start, visited_target)
        if result:
            return result

        result = bfs_step(queue_target, visited_target, visited_start)
        if result:
            return result

    return f"No connection found between '{start_movie_title}' and '{target_movie_title}' via actors."

#GUI code using Tkinter
import tkinter as tk
from tkinter import messagebox

def run_gui():
    #Function to handle the button click
    def on_search():
        start_movie = entry_start_movie.get()
        target_movie = entry_target_movie.get()

        if not start_movie or not target_movie:
            messagebox.showerror("Input Error", "Please enter both movie titles.")
            return

        #Clear the output box before displaying new results
        output_text.delete(1.0, tk.END)

        #Find the shortest path and display it
        result = find_shortest_movie_path(start_movie, target_movie, status_label)
        
        if isinstance(result, list):
            output_text.insert(tk.END, " -> ".join(result))
        else:
            output_text.insert(tk.END, result)

    #Initialise the main window
    root = tk.Tk()
    root.title("Movie Connection Finder")

    #Create and arrange widgets
    label_start_movie = tk.Label(root, text="Enter start movie:")
    label_start_movie.grid(row=0, column=0, padx=10, pady=10)

    entry_start_movie = tk.Entry(root, width=40)
    entry_start_movie.grid(row=0, column=1, padx=10, pady=10)

    label_target_movie = tk.Label(root, text="Enter target movie:")
    label_target_movie.grid(row=1, column=0, padx=10, pady=10)

    entry_target_movie = tk.Entry(root, width=40)
    entry_target_movie.grid(row=1, column=1, padx=10, pady=10)

    search_button = tk.Button(root, text="Find Shortest Path", command=on_search)
    search_button.grid(row=2, column=0, columnspan=2, pady=10)

    status_label = tk.Label(root, text="Pruning: Waiting for input...")
    status_label.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

    output_text = tk.Text(root, height=10, width=60)
    output_text.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

    #Start the Tkinter event loop
    root.mainloop()

#Run the GUI application
if __name__ == "__main__":
    run_gui()
