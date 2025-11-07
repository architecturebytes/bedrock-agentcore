import json

def lambda_handler(event, context):
    # Extract tool name from context
    tool_name = context.client_context.custom.get('bedrockAgentCoreToolName', 'unknown')

    if 'get_order_details' in tool_name:
        order_id = event.get('order_id', 'Unknown')
        # Example static data – in a real app, fetch from DB
        return {
            'statusCode': 200,
            'body': json.dumps({
                'order_id': order_id,
                'order_date': '2025-10-25',
                'product_name': 'Wireless Noise-Cancelling Headphones',
                'quantity': 1,
                'expected_delivery_date': '2025-11-02'
            })
        }

    elif 'get_product_details' in tool_name:
        product_id = event.get('product_id', 'Unknown')
        # Example static data – in a real app, fetch from catalog service
        return {
            'statusCode': 200,
            'body': json.dumps({
                'product_id': product_id,
                'product_name': 'Wireless Noise-Cancelling Headphones',
                'product_description': 'Over-ear Bluetooth headphones with active noise cancellation and 30-hour battery life.'
            })
        }

    else:
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Unknown tool'})
        }
