// src/utils/dayjsConfig.ts
import dayjs from "dayjs";
import timezone from "dayjs/plugin/timezone";
import utc from "dayjs/plugin/utc";

dayjs.extend(utc); // Extend with UTC support
dayjs.extend(timezone); // Extend with timezone support

export default dayjs;
