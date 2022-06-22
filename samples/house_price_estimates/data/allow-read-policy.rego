package dataapi.authz

rule[{}] {
  description := "allow datasets to be read"
  input.action.actionType == "read"
}