import graphene
from crm.schema import Query as CrmQuery, Mutation as CrmMutation


class Query(CrmQuery, graphene.ObjectType):
    """Root Query"""
    pass


class Mutation(CrmMutation, graphene.ObjectType):
    """Root Mutation"""
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
