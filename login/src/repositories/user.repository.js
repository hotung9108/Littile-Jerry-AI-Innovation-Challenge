import { QueryCommand } from '@aws-sdk/lib-dynamodb';
import { ddb } from '../lib/dynamodb.js';

const { USERS_TABLE, EMAIL_INDEX } = process.env;

export const findUserByEmail = async (email) => {
  const { Items } = await ddb.send(new QueryCommand({
    TableName: USERS_TABLE,
    IndexName: EMAIL_INDEX,
    KeyConditionExpression: 'email = :email',
    ExpressionAttributeValues: { ':email': email },
    Limit: 1,
  }));

  return Items?.[0] ?? null;
};
