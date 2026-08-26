Create a small web service for a customer-support assistant. An authenticated
customer's message and retrieved knowledge-base excerpts are sent to an LLM.
The LLM returns JSON with an action (`view_order` or `list_orders`), an optional
order ID, a confidence from 0 to 1, and an answer in Markdown. Execute the
requested read action against a SQL orders database for that customer and
render the answer in the browser. Include implementation and tests.
