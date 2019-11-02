#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: _Rollo
"""

from confluent_kafka.admin import AdminClient, NewTopic

adminConfig = {
                'bootstrap.servers': 'localhost:9092'
              }

topicList = ["manager0", "cluster0", "display"]
partitions = [4, 4, 4]
replications = [1, 1, 1]

if __name__ == '__main__' :
    newTopics = []
    adminClient = AdminClient(adminConfig)
    adminClient.delete_topics(topicList)
    adminClient.delete_topics(["__consumer_offsets"])
    for i in range(len(topicList)):
        newTopics.append(NewTopic(topicList[i], partitions[i] , replications[i]))
    print(newTopics)
    adminClient.create_topics(newTopics)


