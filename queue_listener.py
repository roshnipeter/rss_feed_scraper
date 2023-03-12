import pika
import json
import logging
import db_service


def on_message(channel, method, body):
    try:
        body_json = json.loads(body)
        user_id = body_json['args'][0]
        feedUrl = body_json['args'][1]
        db_service.force_feed_update(user_id, feedUrl)
        logging.info(f"Updated completed for message id:{body_json['message_id']}")
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logging.exception("Error processing message: %s", e)
        channel.basic_reject(delivery_tag=method.delivery_tag, requeue=False)


if __name__ == '__main__':
    credentials = pika.PlainCredentials('guest', 'guest')
    parameters = pika.ConnectionParameters(host='127.0.0.1', port=5672,
                                            credentials=credentials)

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.basic_consume(queue='default', on_message_callback=on_message)
    logging.info("Listening for messages. To exit press CTRL+C")
    channel.start_consuming()
