"use strict";
/**
 * Route index - exports all route creators
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.createA2ARouter = exports.createSessionsRouter = exports.createInfluxDBRouter = exports.createTasksRouter = exports.createStatsRouter = exports.createActionsRouter = exports.createAgentsRouter = void 0;
var agents_1 = require("./agents");
Object.defineProperty(exports, "createAgentsRouter", { enumerable: true, get: function () { return agents_1.createAgentsRouter; } });
var actions_1 = require("./actions");
Object.defineProperty(exports, "createActionsRouter", { enumerable: true, get: function () { return actions_1.createActionsRouter; } });
var stats_1 = require("./stats");
Object.defineProperty(exports, "createStatsRouter", { enumerable: true, get: function () { return stats_1.createStatsRouter; } });
var tasks_1 = require("./tasks");
Object.defineProperty(exports, "createTasksRouter", { enumerable: true, get: function () { return tasks_1.createTasksRouter; } });
var influxdb_1 = require("./influxdb");
Object.defineProperty(exports, "createInfluxDBRouter", { enumerable: true, get: function () { return influxdb_1.createInfluxDBRouter; } });
var sessions_1 = require("./sessions");
Object.defineProperty(exports, "createSessionsRouter", { enumerable: true, get: function () { return sessions_1.createSessionsRouter; } });
var a2a_1 = require("./a2a");
Object.defineProperty(exports, "createA2ARouter", { enumerable: true, get: function () { return a2a_1.createA2ARouter; } });
//# sourceMappingURL=index.js.map