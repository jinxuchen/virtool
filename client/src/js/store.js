/**
 *
 *
 * @copyright 2017 Government of Canada
 * @license MIT
 * @author igboyes
 *
 */

import { createStore, combineReducers, applyMiddleware } from "redux";
import createSagaMiddleware from "redux-saga";

import { virusesReducer } from "./viruses/reducers";
import { accountReducer } from "./nav/reducers";
import settingsReducer from "./settings/reducers";
import usersReducer from "./settings/users/reducers";
import groupsReducer from "./settings/groups/reducers";
import { rootSaga } from "./sagas";

const sagaMiddleware = createSagaMiddleware();

const reducer = combineReducers({
    viruses: virusesReducer,
    settings: settingsReducer,
    users: usersReducer,
    groups: groupsReducer,
    account: accountReducer
});

export const store = createStore(
    reducer,
    applyMiddleware(sagaMiddleware)
);

sagaMiddleware.run(rootSaga);
