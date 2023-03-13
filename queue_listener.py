import pika
import json
import logging
import db_service
import config


def on_message(channel, method, body):
    """
    This method prcesses the incoming messages from a queue. For each message, the user id and feedurl are extracted from the message body and the method 
    force_feed_update is called. Upon completion of processing each message, as an acknowledgement, the delivery tag of the message is returned to the queue. In case
    processing fails, a reject is returned.
    Args
    - channel: a channel object from the pika module that's used to consume messages from the queue.
    - method: message method used to consume messages,
    - body: message body.
    """
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
    credentials = pika.PlainCredentials(config.config['mq_user_id'], config.config['mq_password'])
    parameters = pika.ConnectionParameters(host=config.config['mq_host'], port=config.config['mq_port'],
                                            credentials=credentials)

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.basic_consume(queue='default', on_message_callback=on_message)
    logging.info("Listening for messages. To exit press CTRL+C")
    channel.start_consuming()
