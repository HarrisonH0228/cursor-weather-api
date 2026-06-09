## Asked Cursor and Claude the same question below
"In my Flask app, I made a weather checking site where you can lookup cities and then fetch information from an API, displaying the information, the program converts the city name into a geocode location then gets it from the API, storing it in a cache. Is this the right approach for production, or would you structure it differently?"

1. What did Cursor Chat know that Claude Chat didn't?
- Cursor knew my whole file structure and project because it had access to the whole directory, Claude Chat only knew what I told it which made its answer a little less helpful and specific, it assumed I was making a server wide cache when the cache is only run locally, but it still tried to evaluate the project structure which was nice.
2. What did Claude Chat do better?
- Claude explained WHY using geocode instead of cities is smarter for a project like mine, it explained how weather APIs use coordinates instead of city names. It also told me how caching was a smart idea because weather APIs likely have ratelimits and you want to avoid requesting from it too many times.
3. When would you use each?
- I think I might use Claude for an easier and simpler explanation because Cursor has been giving me super detailed answers when I'm not really ready for them yet. Claude also already has my instructions and knows a lot more about my project than Cursor does (other than direct access to the files)