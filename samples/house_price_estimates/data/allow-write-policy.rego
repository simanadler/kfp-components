package dataapi.authz

rule[{}] {
  description := "allow datasets to be written"
  input.action.actionType == "write"
}