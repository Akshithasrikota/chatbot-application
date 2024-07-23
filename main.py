from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging
import db
import tester

inprogress_orders = {}

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.post("/")
async def handle_request(request: Request):
    try:
        payload = await request.json()  # Ensure payload is awaited correctly
        logger.info(f"Received payload: {payload}")

        intent = payload['queryResult']['intent']['displayName']
        parameters = payload['queryResult']['parameters']
        output_contexts = payload['queryResult']['outputContexts']
        logger.info(f"Intent: {intent}")
        session_id = tester.extract_session_id(output_contexts[0]["name"])

        intent_handler_dict = {
            "order.add-c.ongoingorder": add_to_order,
            # "Order.remove-c.ongoing order": remove_from_order,
            "order.complete-c.ongoingorder": complete_order,
            "track.order-c.ongoing-tracking": track_order
        }

        if intent in intent_handler_dict:
            response = await intent_handler_dict[intent](parameters, session_id)  # Ensure intent handler is awaited
            return response
        else:
            return JSONResponse(content={
                "fulfillmentText": f"No handler found for intent: {intent}"
            }, status_code=400)

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return JSONResponse(content={
            "fulfillmentText": f"Error processing request: {str(e)}"
        }, status_code=400)


async def track_order(parameters: dict, session_id: str):  # Ensure async definition
    try:
        order_id = int(parameters['number'])
        order_status = await db.get_order_status(order_id)  # Await the database call
        if order_status:
            fulfillment_text = f"The order status for order id: {order_id} is: {order_status}"
        else:
            fulfillment_text = f"No order found with order id: {order_id}"

        return JSONResponse(content={
            "fulfillmentText": fulfillment_text
        })

    except Exception as e:
        logger.error(f"Error fetching order status: {str(e)}")
        return JSONResponse(content={
            "fulfillmentText": f"Error fetching order status: {str(e)}"
        }, status_code=500)


async def add_to_order(parameters: dict, session_id: str):  # Ensure async definition
    try:
        food_items = parameters['food-items']
        quantity = parameters['number']
        if len(food_items) != len(quantity):
            fulfillment_text = "Sorry, can you specify food items and quantity?"
        else:
            new_food_dict = dict(zip(food_items, quantity))

            if session_id in inprogress_orders:
                current_food_dict = inprogress_orders[session_id]
                current_food_dict.update(new_food_dict)
                inprogress_orders[session_id] = current_food_dict
            else:
                inprogress_orders[session_id] = new_food_dict

            order_str = tester.get_str_from_food_dict(inprogress_orders[session_id])
            fulfillment_text = f"So far you have {order_str}. Do you need anything else?"

        return JSONResponse(content={
            "fulfillmentText": fulfillment_text
        })

    except Exception as e:
        logger.error(f"Error adding to order: {str(e)}")
        return JSONResponse(content={
            "fulfillmentText": f"Error adding to order: {str(e)}"
        }, status_code=500)


async def complete_order(parameters: dict, session_id: str):
    if session_id not in inprogress_orders:
        fulfillment_text = f"No order found with order id: {session_id}"
    else:
        order = inprogress_orders[session_id]
        order_id = await save_to_db(order)  # Await the save_to_db function

        if order_id == -1:
            fulfillment_text = "Sorry, could not process your order because of backend error. Please place a new order again."
        else:
            order_total = db.get_total_order_price(order_id)
            fulfillment_text = f"Awesome. We have placed your order. Here is your order id: {order_id}. Your order total is {order_total}"
        del inprogress_orders[session_id]

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })


async def save_to_db(order: dict):
    next_order_id = await db.get_next_order_id()  # Await the database call

    for food_item, quantity in order.items():
        rcode = await db.insert_order_item(food_item, quantity, next_order_id)  # Await the database call

        if rcode == -1:
            return -1
    await db.insert_order_tracking(next_order_id, "in progress")  # Await the database call
    return next_order_id

def remove_from_order(parameters: dict, session_id: str):
    if session_id not in inprogress_orders:
        return JSONResponse(content={
            "fulfillmentText": f"No order found with order id"
        })
    current_order = inprogress_orders[session_id]
    food_items = parameters['food-items']
    removed_food_items = []
    no_such_items=[]
    for item in food_items:
        if item not in current_order:
            no_such_items.append(item)
        else:
            removed_food_items.append(item)
            del current_order[item]
    if len(removed_food_items) > 0:
        fulfillment_text = f"Removed {','.join(removed_food_items)}from ur order"
    if len(no_such_items) > 0:
        fulfillment_text = f"your current order doesnot contain: {','.join(no_such_items)}"
    if len(current_order.keys()) == 0:
        fulfillment_text += " Your order is empty!"
    else:
        order_str = tester.get_str_from_food_dict(current_order)
        fulfillment_text += f" Here is what is left in your order: {order_str}"

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


