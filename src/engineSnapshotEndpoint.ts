export function engineSnapshotEndpointFromLocation(
  locationLike: Pick<Location, "href">
): string {
  const url = new URL(locationLike.href);
  return (
    url.searchParams.get("engineSnapshot") ||
    new URL("engine-snapshot.json", url).pathname
  );
}
