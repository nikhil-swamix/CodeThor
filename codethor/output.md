```yaml
openapi: 3.0.0
info:
  title: E-commerce Orders API
  version: 1.0.0
paths:
  /orders:
    get:
      summary: Retrieve a list of orders
      responses:
        '200':
          description: A list of orders
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Order'
    post:
      summary: Create a new order
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Order'
      responses:
        '201':
          description: Order created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Order'
  /orders/{orderId}:
    get:
      summary: Retrieve a specific order by ID
      parameters:
        - name: orderId
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: An order object
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Order'
    put:
      summary: Update an order
      parameters:
        - name: orderId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Order'
      responses:
        '200':
          description: Order updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Order'
    delete:
      summary: Delete an order
      parameters:
        - name: orderId
          in: path
          required: true
          schema:
            type: string
      responses:
        '204':
          description: Order deleted
components:
  schemas:
    Order:
      type: object
      required:
        - id
        - customerId
        - items
        - totalAmount
        - status
      properties:
        id:
          type: string
          description: Unique identifier for the order
        customerId:
          type: string
          description: Unique identifier for the customer
        items:
          type: array
          items:
            $ref: '#/components/schemas/OrderItem'
        totalAmount:
          type: number
          format: float
          description: Total amount of the order
        status:
          type: string
          enum: [pending, processing, shipped, delivered, cancelled]
          description: Status of the order
    OrderItem:
      type: object
      required:
        - productId
        - quantity
        - price
      properties:
        productId:
          type: string
          description: Unique identifier for the product
        quantity:
          type: integer
          description: Quantity of the product in the order
        price:
          type: number
          format: float
          description: Price of the product at the time of the order
```
This schema defines an API for managing orders in an e-commerce system, including endpoints for creating, retrieving, updating, and deleting orders. It also includes a nested schema for `OrderItem` to represent the items within an order.